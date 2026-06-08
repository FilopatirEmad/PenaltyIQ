"""
Analysis Route — POST /api/v1/analyze
========================================
FastAPI route that orchestrates the complete analysis pipeline:

    1. signal_proc.py   → Filter landmark coordinates (Butterworth 6Hz)
    2. calibration.py   → Convert to metric using locked calibration
    3. physics_engine.py → Estimate v0, compute (θv, θh)
    4. ik_solver.py     → Compute player-specific joint targets
    5. digital_twin.py  → Forward verify trajectory
    6. coaching_engine.py → Generate feedback report

All errors are caught, logged, and returned as structured JSON.
No unhandled exceptions propagate to the client.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
import numpy as np
import logging
import asyncio

from api.schemas.response import ok
from api.dependencies import get_current_user
from core.rate_limiter import limiter
from config import settings

from api.schemas.analysis_schema import (
    AnalysisRequest,
    AnalysisResponse,
    PhysicsResult,
    IKResult,
    DigitalTwinResult as DigitalTwinSchema,
    CoachingFeedbackItem,
    ConfidenceScore as ConfidenceScoreSchema,
    InputQualityReport as InputQualitySchema,
    PlayerScore,
    AnalysisSummary,
)
from core.signal_proc import filter_landmark_trajectory
from core.physics_engine import run_physics_pipeline
from core.ik_solver import run_ik_pipeline, LaunchTarget, PlayerSegments
from core.digital_twin import run_digital_twin
from core.coaching_engine import generate_full_coaching_report, compute_player_score
from core.angle_calculator import (
    compute_joint_angles_from_filtered_landmarks,
    compute_angle_timelines,
)
from core.confidence import compute_confidence_score, assess_input_quality

router = APIRouter()
logger = logging.getLogger("penaltyiq.routes.analysis")


# ─── Helper: Extract Landmark Trajectories ────────────────────────────────────

def extract_landmark_trajectories(
    frames: list,
    scale_m_per_px: float
) -> dict[str, dict[str, list[float]]]:
    """
    Build time-series dictionaries for each landmark across all frames.

    Stores NORMALISED [0, 1] coordinates so that angle_calculator.py can
    apply its own Y-inversion and pixel-space projection correctly.
    A separate metric version is used only by the physics engine.

    Parameters
    ----------
    frames : list of AnalysisFrame
    scale_m_per_px : float — calibrated scale [m/pixel] (unused here, kept for API compat)

    Returns
    -------
    dict: {landmark_name: {"x": [x_norm_frame0, ...], "y": [y_norm_frame0, ...]}}
    """
    trajectories: dict[str, dict[str, list[float]]] = {}

    for frame in frames:
        for lm_name, lm in frame.landmarks.items():
            if lm_name not in trajectories:
                trajectories[lm_name] = {"x": [], "y": []}
            trajectories[lm_name]["x"].append(lm.x_norm)
            trajectories[lm_name]["y"].append(lm.y_norm)

    return trajectories


def extract_ball_positions(
    frames: list,
    scale_m_per_px: float,
    contact_frame_index: int | None = None
) -> list[tuple[float, float]]:
    """
    Extract ball centre pixel positions from frames that have detections.
    Returns up to 4 positions (need 4 for v0 estimation). [SPEC §2.4]
    """
    ball_positions_px: list[tuple[float, float]] = []

    start_idx = contact_frame_index if contact_frame_index is not None else 0
    for frame in frames:
        if frame.frame_index < start_idx:
            continue
        if frame.ball_center_px is not None:
            ball_positions_px.append((
                frame.ball_center_px.x_px,
                frame.ball_center_px.y_px
            ))
        if len(ball_positions_px) >= 4:
            break

    return ball_positions_px


# ─── Route Handler ────────────────────────────────────────────────────────────

@router.post(
    "/analyze",
    status_code=status.HTTP_200_OK,
    summary="Full Biomechanical Analysis Pipeline",
    description=(
        "Runs the complete PenaltyIQ pipeline: "
        "Butterworth filtering → v0 estimation → inverse projectile physics → "
        "constrained IK (SLSQP) → digital twin verification → coaching feedback."
    ),
)
@limiter.limit(settings.rate_limit_analyze)
async def analyze(
    request: Request,
    analysis_body: AnalysisRequest,
    _user=Depends(get_current_user),
) -> dict:
    """
    POST /analyze

    Requires a valid calibration (status=LOCKED) to have been completed
    for this session_id before calling this endpoint.
    """
    logger.info(
        f"Analysis request: session={analysis_body.session_id}, "
        f"zone={analysis_body.goal_zone}, frames={len(analysis_body.frames)}, "
        f"fps={analysis_body.fps}"
    )

    # Alias to 'request' so the 400-line pipeline body is unchanged
    request = analysis_body  # type: ignore[assignment]  # noqa: F841

    all_warnings: list[str] = []

    # ── Stage 1: Signal Processing (Butterworth LPF) ─────────────────────────
    try:
        raw_trajectories = extract_landmark_trajectories(
            request.frames,
            request.calibration.scale_m_per_px
        )

        # Apply 2nd-order Butterworth LPF to each landmark coordinate
        # [SPEC §1.4.1][WINTER-2009 Ch.3]
        filtered_trajectories: dict[str, dict[str, np.ndarray]] = {}
        for lm_name, coords in raw_trajectories.items():
            if len(coords["x"]) >= 15:
                x_f, y_f = filter_landmark_trajectory(
                    coords["x"], coords["y"], detected_fps=request.fps
                )
                filtered_trajectories[lm_name] = {"x": x_f.tolist(), "y": y_f.tolist()}
            else:
                filtered_trajectories[lm_name] = {
                    "x": list(coords["x"]),
                    "y": list(coords["y"])
                }
                all_warnings.append(
                    f"Landmark '{lm_name}': insufficient frames for Butterworth "
                    f"filter ({len(coords['x'])} < 15). Using raw coordinates."
                )

        logger.info(
            f"Signal processing complete: {len(filtered_trajectories)} "
            f"landmarks filtered."
        )

        # Count how many landmarks had enough frames for Butterworth
        _butterworth_count = sum(
            1 for name, coords in raw_trajectories.items()
            if len(coords["x"]) >= 15
        )

    except Exception as e:
        logger.exception(f"Signal processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Signal processing error: {str(e)}"
        )

    # ── Stage 2: Joint Angle Extraction (Sports2D-on-MediaPipe) ──────────────
    event_kinematics = None
    frame_width  = request.frames[0].frame_width_px
    frame_height = request.frames[0].frame_height_px
    # Infer kicking side from session metadata (default RIGHT)
    kicking_side = getattr(request, "kicking_side", "RIGHT") or "RIGHT"

    try:
        # Angles at single contact frame (for coaching engine)
        measured_angles = await asyncio.to_thread(
            compute_joint_angles_from_filtered_landmarks,
            filtered_trajectories,
            request.contact_frame_index,
            kicking_side,
            frame_width,
            frame_height,
        )

        # Full time-series with Savitzky-Golay smoothing
        angle_timelines, raw_timelines = await asyncio.to_thread(
            compute_angle_timelines,
            filtered_trajectories,
            kicking_side,
            frame_width,
            frame_height,
            request.fps,
        )

        from core.angle_calculator import detect_contact_event
        from api.schemas.analysis_schema import StrictBiomechanicsResult

        # Ankle velocity series: pixel space, Y-inverted (matches angle_calculator)
        k_side   = "RIGHT" if kicking_side.upper() == "RIGHT" else "LEFT"
        k_ankle  = filtered_trajectories.get(f"{k_side}_ANKLE", {"x": [], "y": []})
        ax = [v * frame_width  for v in k_ankle.get("x", [])]
        ay = [(1.0 - v) * frame_height for v in k_ankle.get("y", [])]  # Y-inverted

        strict_biomechanics = None
        if ax:
            strict_biomech_dict = await asyncio.to_thread(
                detect_contact_event,
                angle_timelines, raw_timelines, ax, ay, request.fps
            )
            if strict_biomech_dict:
                try:
                    strict_biomechanics = StrictBiomechanicsResult(**strict_biomech_dict)
                except Exception as e:
                    logger.warning(f"StrictBiomechanicsResult parse error: {e}")

        logger.info("Joint angles extracted: %s", measured_angles)
    except Exception as e:
        logger.exception("Joint angle extraction failed: %s", e)
        measured_angles = {}
        angle_timelines = {}
        strict_biomechanics = None
        all_warnings.append(f"Joint angle extraction warning: {str(e)}")

    # Compress keypoints for frontend overlay
    compressed_keypoints = {}
    for lm_name, coords in filtered_trajectories.items():
        compressed_keypoints[lm_name] = [
            [round(x, 4), round(y, 4)]
            # Fix: Since we removed pandas, filtered_trajectories might already be lists, or numpy arrays.
            # Convert explicitly using list() or just zip directly if they are already iterable arrays/lists
            for x, y in zip(
                coords["x"] if isinstance(coords["x"], list) else coords["x"].tolist() if hasattr(coords["x"], "tolist") else list(coords["x"]), 
                coords["y"] if isinstance(coords["y"], list) else coords["y"].tolist() if hasattr(coords["y"], "tolist") else list(coords["y"])
            )
        ]

    # ── Stage 3: Physics Engine ───────────────────────────────────────────────
    try:
        ball_positions_px = extract_ball_positions(
            request.frames,
            request.calibration.scale_m_per_px,
            request.contact_frame_index
        )

        if len(ball_positions_px) < 4:
            raise ValueError(
                f"Insufficient ball detections for v0 estimation: "
                f"{len(ball_positions_px)}/4 required. "
                f"Ensure ball is visible in at least 4 frames after contact."
            )

        physics_result = await asyncio.to_thread(
            run_physics_pipeline,
            ball_positions_px=ball_positions_px,
            scale_m_per_px=request.calibration.scale_m_per_px,
            zone_id=request.goal_zone,
            fps=request.fps
        )
        all_warnings.extend(physics_result.warnings)

        # Count post-contact ball detections (used for confidence score)
        _post_contact_detections = len(ball_positions_px)

        logger.info(
            f"Physics: v0={physics_result.v0_ms:.3f}m/s, "
            f"θv={physics_result.launch_angles.theta_v_deg:.3f}°, "
            f"θh={physics_result.launch_angles.theta_h_deg:.3f}°, "
            f"regime={physics_result.speed_regime}"
        )

    except ValueError as e:
        logger.error(f"Physics engine error: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Physics engine error: {str(e)}"
        )
    except Exception as e:
        logger.exception(f"Unexpected physics error: {e}")
        raise HTTPException(status_code=500, detail=f"Physics error: {str(e)}")

    # ── Stage 4: IK Solver ────────────────────────────────────────────────────
    try:
        launch_target = LaunchTarget(
            theta_v_rad=physics_result.launch_angles.theta_v_rad,
            theta_h_rad=physics_result.launch_angles.theta_h_rad,
            v0_ms=physics_result.v0_ms,
            zone_id=request.goal_zone
        )
        player_segments = PlayerSegments(
            thigh_m=request.calibration.thigh_m,
            shank_m=request.calibration.shank_m,
            trunk_m=request.calibration.trunk_m,
            leg_m=request.calibration.leg_m
        )
        ik_solution = await asyncio.to_thread(
            run_ik_pipeline, launch_target, player_segments
        )
        all_warnings.extend(ik_solution.warnings)

        logger.info(
            f"IK: hip={ik_solution.hip_flexion_deg:.1f}°, "
            f"knee={ik_solution.knee_flexion_deg:.1f}°, "
            f"ankle={ik_solution.ankle_plantarflexion_deg:.1f}°, "
            f"residual={ik_solution.residual:.6f}, "
            f"quality={ik_solution.convergence_quality}"
        )

    except Exception as e:
        logger.exception(f"IK solver error: {e}")
        raise HTTPException(status_code=500, detail=f"IK solver error: {str(e)}")

    # ── Stage 5: Digital Twin Verification ───────────────────────────────────
    try:
        twin_result = await asyncio.to_thread(
            run_digital_twin,
            v0_ms=physics_result.v0_ms,
            theta_v_rad=physics_result.launch_angles.theta_v_rad,
            theta_h_rad=physics_result.launch_angles.theta_h_rad,
            target_zone_id=request.goal_zone
        )
        all_warnings.extend(twin_result.warnings)

        logger.info(
            f"Digital twin: hit={twin_result.nominal.hit_zone}, "
            f"passed={twin_result.nominal.verification_passed}, "
            f"robust={twin_result.robust_under_perturbation}"
        )

    except Exception as e:
        logger.exception(f"Digital twin error: {e}")
        all_warnings.append(f"Digital twin verification unavailable: {str(e)}")
        twin_result = None

    # ── Stage 6: Coaching Engine ──────────────────────────────────────────────
    try:
        ik_targets = {
            "hip_flexion":          ik_solution.hip_flexion_deg,
            "knee_flexion":         ik_solution.knee_flexion_deg,
            "ankle_plantarflexion": ik_solution.ankle_plantarflexion_deg,
            "support_knee":         ik_solution.support_knee_deg,
            "trunk_inclination":    ik_solution.trunk_inclination_deg,
        }

        coaching_items = await asyncio.to_thread(
            generate_full_coaching_report,
            zone_id=request.goal_zone,
            measured_angles=measured_angles,
            ik_targets=ik_targets
        )

        logger.info(
            f"Coaching report: {len(coaching_items)} items generated."
        )

    except Exception as e:
        logger.exception(f"Coaching engine error: {e}")
        coaching_items = []
        all_warnings.append(f"Coaching engine error: {str(e)}")

    # ── Compute Confidence Score ────────────────────────────────────────────
    try:
        # Mean visibility: average over all landmark trajectories at all frames
        _all_visibilities = [
            lm.visibility
            for frame in request.frames
            for lm in frame.landmarks.values()
        ]
        _mean_visibility = (
            sum(_all_visibilities) / len(_all_visibilities)
            if _all_visibilities else 0.5
        )

        # Ball detection rate across submitted analysis frames
        _total_frames = len(request.frames)
        _frames_with_ball = sum(
            1 for f in request.frames if f.ball_center_px is not None
        )
        _ball_rate = _frames_with_ball / _total_frames if _total_frames > 0 else 0.0

        _pose_rate = sum(
            1 for f in request.frames if f.landmarks
        ) / _total_frames if _total_frames > 0 else 0.0

        _confidence_raw = compute_confidence_score(
            gate_passed=request.calibration.gate_passed,
            gate_passed_with_fallback=request.calibration.gate_passed_with_fallback,
            fallback_reason=request.calibration.fallback_reason,
            thigh_variation_m=request.calibration.thigh_variation_m,
            thigh_tolerance_m=request.calibration.thigh_tolerance_m,
            calib_frames_used=request.calibration.frames_used,
            pose_detection_rate=_pose_rate,
            mean_landmark_visibility=_mean_visibility,
            frames_filtered_with_butterworth=_butterworth_count,
            total_analysis_frames=_total_frames,
            ball_detection_rate=_ball_rate,
            post_contact_detections=_post_contact_detections,
        )

        confidence_schema = ConfidenceScoreSchema(
            overall=_confidence_raw.overall,
            level=_confidence_raw.level,
            calibration_score=_confidence_raw.calibration_score,
            pose_score=_confidence_raw.pose_score,
            ball_score=_confidence_raw.ball_score,
            calibration_detail=_confidence_raw.calibration_detail,
            pose_detail=_confidence_raw.pose_detail,
            ball_detail=_confidence_raw.ball_detail,
            summary=_confidence_raw.summary,
        )

        _quality_raw = assess_input_quality(
            pose_detection_rate=_pose_rate,
            ball_detection_rate=_ball_rate,
            post_contact_detections=_post_contact_detections,
            fps=request.fps,
            calibration_gate_passed=(
                request.calibration.gate_passed
                or request.calibration.gate_passed_with_fallback
            ),
            calibration_fallback_reason=request.calibration.fallback_reason,
        )

        quality_schema = InputQualitySchema(
            usable=_quality_raw.usable,
            quality_level=_quality_raw.quality_level,
            issues=_quality_raw.issues,
            user_messages=_quality_raw.user_messages,
            suggestions=_quality_raw.suggestions,
        )

        # Surface quality warnings into pipeline_warnings so they appear
        # even in clients that don’t inspect the confidence field.
        if _quality_raw.quality_level in ("POOR", "UNUSABLE"):
            for msg in _quality_raw.user_messages:
                if msg not in all_warnings:
                    all_warnings.append(msg)

    except Exception as e:
        logger.exception(f"Confidence scoring failed (non-fatal): {e}")
        confidence_schema = None
        quality_schema = None

    # ── Assemble Response ─────────────────────────────────────────────────────
    physics_schema = PhysicsResult(
        v0_measured_ms=round(physics_result.v0_ms, 3),
        theta_v_deg=round(physics_result.launch_angles.theta_v_deg, 3),
        theta_h_deg=round(physics_result.launch_angles.theta_h_deg, 3),
        speed_regime=physics_result.speed_regime,
        feasibility=physics_result.feasibility,
        crossbar_clearance_m=round(physics_result.crossbar_clearance_m, 4),
        safety_margin_satisfied=physics_result.safety_margin_satisfied
    )

    ik_schema = IKResult(
        hip_flexion_deg=round(ik_solution.hip_flexion_deg, 2),
        knee_angle_deg=round(ik_solution.knee_flexion_deg, 2),
        ankle_plantarflexion_deg=round(ik_solution.ankle_plantarflexion_deg, 2),
        support_leg_knee_deg=round(ik_solution.support_knee_deg, 2),
        trunk_inclination_deg=round(ik_solution.trunk_inclination_deg, 2),
        solver_converged=ik_solution.converged,
        residual=round(ik_solution.residual, 6)
    )

    twin_schema = None
    if twin_result is not None:
        twin_schema = DigitalTwinSchema(
            predicted_x_m=round(twin_result.nominal.z_at_goal_m, 4),
            predicted_y_m=round(twin_result.nominal.y_at_goal_m, 4),
            zone_hit=twin_result.nominal.hit_zone,
            verification_passed=twin_result.nominal.verification_passed,
            x_error_m=round(twin_result.nominal.z_error_m, 4),
            y_error_m=round(twin_result.nominal.y_error_m, 4)
        )

    coaching_schema = [
        CoachingFeedbackItem(
            variable=item.variable,
            measured_deg=item.measured_deg,
            target_deg=item.target_deg,
            target_range_min_deg=item.target_range_min_deg,
            target_range_max_deg=item.target_range_max_deg,
            delta_deg=item.delta_deg,
            status=item.status,
            cue=item.cue
        )
        for item in coaching_items
    ]

    player_score_data = compute_player_score(coaching_items, physics_result.v0_ms)
    player_score_schema = PlayerScore(
        score=player_score_data["score"],
        level=player_score_data["level"],
        breakdown=player_score_data["breakdown"]
    )

    # Build top insight for summary
    top_insight = "Great technique!"
    if coaching_items:
        # Items are already sorted by severity in coaching_engine
        worst_item = coaching_items[0]
        if worst_item.status in ("CRITICAL", "NEEDS_WORK"):
            top_insight = worst_item.cue
            
    summary_schema = None
    if twin_schema:
        summary_schema = AnalysisSummary(
            player_score=player_score_data["score"],
            player_level=player_score_data["level"],
            top_insight=top_insight,
            ball_speed_kmh=round(physics_result.v0_ms * 3.6, 1),
            target_hit=twin_result.nominal.verification_passed,
            zone_hit=twin_result.nominal.hit_zone
        )

    result = AnalysisResponse(
        session_id=request.session_id,
        goal_zone=request.goal_zone,
        contact_frame_index=request.contact_frame_index,
        physics=physics_schema,
        ik_result=ik_schema,
        strict_biomechanics=strict_biomechanics,
        digital_twin=twin_schema,
        coaching_feedback=coaching_schema,
        pipeline_warnings=all_warnings,
        confidence=confidence_schema,
        input_quality=quality_schema,
        player_score=player_score_schema,
        angle_timelines=angle_timelines,
        compressed_keypoints=compressed_keypoints,
        summary=summary_schema,
    )
    return ok(data=result.model_dump(), message="Analysis complete.")