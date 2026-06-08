"""
Video Upload Route — POST /api/v1/process-video
=================================================
Accepts a raw video file upload, runs the complete pipeline:
    1. MediaPipe Pose extraction (all frames)
    2. HoughCircles ball detection (all frames)
    3. Contact frame detection
    4. Calibration payload construction (first N frames)
    5. Analysis payload construction (contact + post-contact frames)

Returns both calibration data and analysis frames in a single response,
enabling the Flutter frontend to submit them to /calibrate and /analyze.

This endpoint is an optimisation: avoids two separate video uploads.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import JSONResponse, FileResponse
import json
import logging
import asyncio
import os
import gc
import tempfile
from contextlib import suppress

from core.pose_estimator import (
    PoseEstimator,
    build_calibration_frame_payload,
    ANALYSIS_REQUIRED_LANDMARKS,
)
from core.ball_detector import (
    detect_ball_in_frame,
    detect_contact_frame,
)
from core.calibration import run_calibration_pipeline
from core.confidence import assess_input_quality
from core.visualizer import render_overlay_video
from api.schemas.response import ok
from api.dependencies import get_current_user
from core.rate_limiter import limiter
from config import settings

router = APIRouter()
logger = logging.getLogger("penaltyiq.routes.video")


@router.post(
    "/process-video",
    status_code=status.HTTP_200_OK,
    summary="Upload video for complete pose + ball extraction",
    description=(
        "Accepts a video file upload. Runs MediaPipe Pose and "
        "HoughCircles ball detection. Returns structured frame data "
        "for /calibrate and /analyze endpoints."
    ),
)
@limiter.limit(settings.rate_limit_video)
async def process_video(
    request: Request,
    video: UploadFile = File(..., description="Video file (MP4/MOV, 60fps)"),
    session_id: str = Form(..., description="UUID v4 session identifier"),
    goal_zone: str  = Form(..., description="Target zone (T1–B4)"),
    mode: str       = Form(
        default="full",
        description="'calibration' | 'analysis' | 'full'"
    ),
    _user=Depends(get_current_user),
) -> JSONResponse:
    """
    POST /process-video

    Accepts multipart form data with:
        - video: raw video bytes
        - session_id: UUID
        - goal_zone: target zone
        - mode: processing mode

    Returns JSON with extracted calibration and analysis frame data.
    """
    # ── Validate file type ────────────────────────────────────────────────
    ALLOWED_CONTENT_TYPES = {
        "video/mp4",
        "video/quicktime",
        "video/x-msvideo",
        "video/avi",
        "video/webm",
        "application/octet-stream",
    }
    if video.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Invalid video format: {video.content_type}. "
                f"Accepted formats: MP4, MOV, AVI."
            )
        )

    # ── Stream video to temp file (no full-RAM load) ─────────────────────
    MAX_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500 MB
    CHUNK_SIZE = 1024 * 1024  # 1 MB per chunk

    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_stream:
        tmp_path = tmp_stream.name
        bytes_written = 0
        while True:
            chunk = await video.read(CHUNK_SIZE)
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > MAX_FILE_SIZE_BYTES:
                with suppress(FileNotFoundError):
                    os.unlink(tmp_path)
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"Video file too large (> {MAX_FILE_SIZE_BYTES/1e6:.0f}MB). "
                        f"Please trim the clip and retry."
                    )
                )
            tmp_stream.write(chunk)

    logger.info(
        f"Video processing request: session={session_id}, "
        f"zone={goal_zone}, mode={mode}, "
        f"size={bytes_written/1e6:.1f}MB, "
        f"content_type={video.content_type}"
    )

    warnings: list[str] = []

    try:
        # ── Stage 1: MediaPipe Pose extraction ────────────────────────────
        with PoseEstimator() as estimator:
            pose_result = await asyncio.to_thread(
                estimator.process_video_bytes_from_path, tmp_path
            )

        warnings.extend(pose_result.warnings)
        logger.info(
            f"Pose extraction: {pose_result.frames_with_pose}/"
            f"{pose_result.total_frames_processed} frames detected, "
            f"fps={pose_result.fps:.1f}"
        )

        if pose_result.pose_detection_rate < 0.5:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Pose detection rate too low: "
                    f"{pose_result.pose_detection_rate:.1%}. "
                    f"Ensure the player is fully visible in the sagittal "
                    f"plane with no significant occlusion."
                )
            )

        # ── Stage 2: Ball detection — streaming, no full frame list ───────
        # Frames are processed one at a time from the shared temp file.
        # Peak RAM = one BGR frame (~6 MB for 1080p) rather than the
        # entire video (~600 MB for 10 s @ 60 fps @ 1080p).
        def _stream_ball_detection(path: str) -> list:
            import cv2 as _cv2
            cap = _cv2.VideoCapture(path)
            detections = []
            frame_idx = 0
            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break
                det = detect_ball_in_frame(frame_bgr, expected_diameter_px=None)
                detections.append(det)
                frame_idx += 1
            cap.release()
            return detections

        ball_detections = await asyncio.to_thread(
            _stream_ball_detection, tmp_path
        )
        total_video_frames = len(ball_detections)

        # temp file no longer needed after ball detection
        with suppress(FileNotFoundError):
            os.unlink(tmp_path)

        detected_count = sum(1 for d in ball_detections if d is not None)
        logger.info(
            f"Ball detection: {detected_count}/{total_video_frames} frames."
        )

        # Extract ball diameters per frame
        ball_diameters_px = [
            d.diameter_px if d is not None else 0.0
            for d in ball_detections
        ]

        # ── Stage 3: Build calibration frames ─────────────────────────────
        calib_frames = build_calibration_frame_payload(
            pose_result=pose_result,
            ball_diameters_px=ball_diameters_px
        )

        # ── Stage 4: Run calibration gate ─────────────────────────────────
        calib_request_data = {
            "session_id": session_id,
            "frames": calib_frames
        }
        calib_result = await asyncio.to_thread(
            run_calibration_pipeline, calib_request_data
        )

        # Snapshot scalars we need after pose_result is freed
        result_fps                  = pose_result.fps
        result_total_frames         = pose_result.total_frames_processed
        result_pose_detection_rate  = pose_result.pose_detection_rate

        # ── Stage 5: Contact frame detection ──────────────────────────────
        contact_frame_idx = await asyncio.to_thread(
            detect_contact_frame, ball_detections, result_fps, pose_result
        )

        # ── Stage 6: Build analysis frames ────────────────────────────────
        # Only emit landmarks needed for kick analysis (prunes ~60% of
        # landmark data per frame, cutting JSON size significantly).
        # ball_center_px is only included at/after contact frame to
        # avoid sending redundant pre-kick ball positions.
        analysis_frames = []
        for pose_frame in pose_result.frames:
            if not pose_frame.pose_detected:
                continue

            frame_idx = pose_frame.frame_index
            is_contact_or_after = (
                contact_frame_idx is not None
                and frame_idx >= contact_frame_idx
            )
            ball_det = (
                ball_detections[frame_idx]
                if (is_contact_or_after and frame_idx < len(ball_detections))
                else None
            )

            # Only include the landmarks required for biomechanical analysis
            landmarks_dict = {
                name: {
                    "x_norm": round(lm.x_norm, 5),
                    "y_norm": round(lm.y_norm, 5),
                    "visibility": round(lm.visibility, 3),
                }
                for name, lm in pose_frame.landmarks.items()
                if name in ANALYSIS_REQUIRED_LANDMARKS
            }

            frame_data: dict = {
                "frame_index":    pose_frame.frame_index,
                "timestamp_ms":   round(pose_frame.timestamp_ms, 1),
                "landmarks":      landmarks_dict,
                "frame_width_px":  pose_frame.frame_width_px,
                "frame_height_px": pose_frame.frame_height_px,
            }
            if ball_det is not None:
                frame_data["ball_center_px"] = {
                    "x_px": round(ball_det.x_centre_px, 1),
                    "y_px": round(ball_det.y_centre_px, 1),
                }
            analysis_frames.append(frame_data)

        # Release the large PoseFrame list before JSON serialisation
        del pose_result
        gc.collect()

        # ── Input quality assessment ────────────────────────────────────────────
        # Computed here (pre-analysis) so the UI can show warnings
        # before the user decides whether to submit for analysis.
        _ball_rate = detected_count / total_video_frames if total_video_frames > 0 else 0.0
        _pose_rate = result_pose_detection_rate   # captured before del pose_result

        # Count post-contact ball detections available
        _post_contact = sum(
            1 for i, d in enumerate(ball_detections)
            if d is not None
            and contact_frame_idx is not None
            and i >= contact_frame_idx
        )

        try:
            _quality = assess_input_quality(
                pose_detection_rate=_pose_rate,
                ball_detection_rate=_ball_rate,
                post_contact_detections=_post_contact,
                fps=result_fps,
                calibration_gate_passed=(
                    calib_result.gate_passed
                    or calib_result.gate_passed_with_fallback
                ),
                calibration_fallback_reason=calib_result.fallback_reason,
            )
            input_quality_payload = {
                "usable":         _quality.usable,
                "quality_level":  _quality.quality_level,
                "issues":         _quality.issues,
                "user_messages":  _quality.user_messages,
                "suggestions":    _quality.suggestions,
            }
            # Promote POOR/UNUSABLE issues into top-level warnings
            if _quality.quality_level in ("POOR", "UNUSABLE"):
                for msg in _quality.user_messages:
                    if msg not in warnings:
                        warnings.append(msg)
        except Exception as _qe:
            logger.warning(f"Input quality assessment failed (non-fatal): {_qe}")
            input_quality_payload = None

        # ── Assemble response ──────────────────────────────────────────────
        # segments_m is populated when gate passed OR fallback succeeded,
        # allowing downstream analysis to proceed in both cases.
        calib_usable = calib_result.gate_passed or calib_result.gate_passed_with_fallback
        response_payload = {
            "session_id":          session_id,
            "goal_zone":           goal_zone,
            "fps":                 result_fps,
            "total_frames":        result_total_frames,
            "contact_frame_index": contact_frame_idx,
            "calibration": {
                "gate_passed":               calib_result.gate_passed,
                "gate_passed_with_fallback": calib_result.gate_passed_with_fallback,
                "fallback_reason":           calib_result.fallback_reason,
                "scale_m_per_px":            calib_result.scale_m_per_px,
                "segments_m": (
                    {
                        "thigh_m":          calib_result.thigh_m,
                        "shank_m":          calib_result.shank_m,
                        "trunk_m":          calib_result.trunk_m,
                        "leg_m":            calib_result.leg_m,
                        "thigh_variation_m": calib_result.thigh_variation_m,
                        "thigh_tolerance_m": calib_result.thigh_tolerance_m,
                        "frames_used":       calib_result.frames_used,
                    }
                    if calib_usable else None
                ),
                "stability_check": {
                    "thigh_variation_m":  calib_result.thigh_variation_m,
                    "shank_variation_m":  calib_result.shank_variation_m,
                    "trunk_variation_m":  calib_result.trunk_variation_m,
                    "thigh_tolerance_m":  calib_result.thigh_tolerance_m,
                    "shank_tolerance_m":  calib_result.shank_tolerance_m,
                    "trunk_tolerance_m":  calib_result.trunk_tolerance_m,
                    "window_duration_s":  calib_result.window_duration_s,
                    "overall_passed":     calib_result.gate_passed,
                },
                "error": calib_result.error_message,
            },
            "input_quality":          input_quality_payload,
            "analysis_frames_count": len(analysis_frames),
            "analysis_frames":       analysis_frames,
            "warnings":              warnings,
        }

        return JSONResponse(content=ok(
            data=response_payload,
            message="Video processed successfully."
        ))

    except ValueError as e:
        logger.warning(f"Video validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Video processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing error: {str(e)}"
        )
    finally:
        # Guarantee temp file cleanup even on unhandled exceptions
        with suppress(FileNotFoundError, UnboundLocalError):
            os.unlink(tmp_path)


@router.post(
    "/render-video",
    summary="Generate an overlaid analysis video",
    description="Takes a raw video and an AnalysisResponse JSON to draw skeleton, angles, and score.",
)
@limiter.limit(settings.rate_limit_render)
async def render_video_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    analysis_data: str = Form(...),
    scale_m_per_px: float = Form(
        ...,
        description="Calibrated scale factor [m/pixel] from /process-video calibration response.",
        gt=0.0
    ),
    _user=Depends(get_current_user),
):
    """
    POST /render-video

    Renders a skeleton-overlay video using the provided analysis result.
    The scale_m_per_px must be forwarded from the calibration.scale_m_per_px
    field returned by /process-video.

    The output temp file is cleaned up automatically after the response is sent.
    """
    tmp_path: str | None = None
    out_path: str | None = None
    try:
        data = json.loads(analysis_data)

        # Save uploaded video to temp file
        fd, tmp_path = tempfile.mkstemp(suffix=".mp4")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(await video.read())

        # Render video overlay
        out_path = await asyncio.to_thread(
            render_overlay_video, tmp_path, data, scale_m_per_px
        )

        # Clean up input immediately — output is served then cleaned via background task
        with suppress(FileNotFoundError):
            os.unlink(tmp_path)
            tmp_path = None

        # Schedule output file deletion after response is fully sent
        background_tasks.add_task(_cleanup_temp_file, out_path)

        return FileResponse(
            out_path,
            media_type="video/mp4",
            filename="analysis_render.mp4"
        )
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid analysis_data JSON: {e}"
        )
    except Exception as e:
        logger.exception(f"Render video failed: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e), "data": None}
        )
    finally:
        if tmp_path:
            with suppress(FileNotFoundError):
                os.unlink(tmp_path)


def _cleanup_temp_file(path: str) -> None:
    """Background task: delete a temp file after the response has been sent."""
    with suppress(FileNotFoundError, TypeError):
        if path:
            os.unlink(path)
            logger.debug(f"Cleaned up temp file: {path}")