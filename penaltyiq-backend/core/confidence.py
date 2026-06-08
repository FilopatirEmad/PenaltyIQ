"""
Confidence Scoring — PenaltyIQ Backend
========================================
Computes a composite confidence score ∈ [0, 1] for every analysis result.

The score is composed of three independent sub-scores:

    confidence = w_calib × S_calib  +  w_pose × S_pose  +  w_ball × S_ball

Weights [MODEL]:
    w_calib = 0.40   (calibration is the scale reference — highest impact)
    w_pose  = 0.35   (landmark quality drives IK accuracy)
    w_ball  = 0.25   (ball detection drives v0 accuracy)

Each sub-score ∈ [0, 1]:
    S_calib  — based on calibration gate tier and variation/tolerance ratio
    S_pose   — based on pose detection rate and mean landmark visibility
    S_ball   — based on ball detection rate and post-contact coverage

The score is mapped to a human-readable confidence level:
    EXCELLENT  ≥ 0.85
    GOOD       ≥ 0.70
    FAIR       ≥ 0.50
    LOW        < 0.50

Scientific basis:
    [MODEL]: Weights chosen to reflect biomechanical sensitivity analysis.
    Calibration error → linear scale error in all metric quantities.
    Pose error        → IK angle error (non-linear but bounded by constraints).
    Ball error        → v0 error (largest relative impact on trajectory).
"""

import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger("penaltyiq.confidence")

# ── Weights ───────────────────────────────────────────────────────────────────
_W_CALIB: float = 0.40
_W_POSE:  float = 0.35
_W_BALL:  float = 0.25

assert abs(_W_CALIB + _W_POSE + _W_BALL - 1.0) < 1e-9, "Weights must sum to 1.0"

# ── Calibration tier penalties ─────────────────────────────────────────────────
_CALIB_TIER_SCORES: dict[str, float] = {
    "strict":                     1.00,   # full gate passed at 2%
    "relaxed_tolerance_5pct":     0.80,   # passed at 5% — slightly noisy
    "anthropometric_short_clip":  0.55,   # Winter-2009 fallback, some data available
    "anthropometric_unstable":    0.45,   # Winter-2009 fallback, data present but noisy
    "anthropometric_too_few_frames": 0.30, # almost no valid frames
}


@dataclass
class ConfidenceScore:
    """
    Composite confidence score for a single analysis result.

    All sub-scores and the overall score are ∈ [0, 1].
    """
    overall: float          # weighted composite ∈ [0, 1]
    level: str              # EXCELLENT | GOOD | FAIR | LOW
    calibration_score: float
    pose_score: float
    ball_score: float

    # Per-component explanations — displayed in the UI
    calibration_detail: str
    pose_detail: str
    ball_detail: str

    # Aggregated user-facing message (single sentence)
    summary: str


def _level(score: float) -> str:
    if score >= 0.85:
        return "EXCELLENT"
    if score >= 0.70:
        return "GOOD"
    if score >= 0.50:
        return "FAIR"
    return "LOW"


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))


# ── Sub-score: Calibration ─────────────────────────────────────────────────────

def _calibration_sub_score(
    gate_passed: bool,
    gate_passed_with_fallback: bool,
    fallback_reason: Optional[str],
    thigh_variation_m: float,
    thigh_tolerance_m: float,
    frames_used: int,
) -> tuple[float, str]:
    """
    Compute S_calib and its human-readable explanation.

    When the gate passes cleanly, we further scale by the
    variation/tolerance ratio — a score of 0.5× tolerance = near-perfect.
    """
    if gate_passed and not gate_passed_with_fallback:
        # Strict gate passed — scale by how close to tolerance
        tier_score = _CALIB_TIER_SCORES["strict"]
        if thigh_tolerance_m > 0:
            ratio = thigh_variation_m / thigh_tolerance_m  # 0 = perfect, 1 = just passed
            # Score degrades linearly from 1.0 to 0.85 as ratio → 1.0
            tier_score = 1.0 - 0.15 * _clamp(ratio)
        detail = (
            f"Calibration passed (strict). "
            f"{frames_used} frames used. "
            f"Segment stability: {(1 - thigh_variation_m / max(thigh_tolerance_m, 1e-6)):.0%} within tolerance."
        )
        return _clamp(tier_score), detail

    if gate_passed_with_fallback and fallback_reason:
        tier_score = _CALIB_TIER_SCORES.get(fallback_reason, 0.40)
        friendly = {
            "relaxed_tolerance_5pct":
                f"Calibration passed with relaxed tolerance (5%). "
                f"Video had elevated landmark jitter. "
                f"Segment estimates are slightly less precise — reshoot for best accuracy.",
            "anthropometric_short_clip":
                f"Calibration used population averages (Winter 2009) — "
                f"clip too short ({frames_used} frames). "
                f"Hold T-pose for ≥ 2 seconds for player-specific measurements.",
            "anthropometric_unstable":
                f"Calibration used population averages (Winter 2009) — "
                f"T-pose was unstable across {frames_used} frames. "
                f"Stand still and keep all joints visible during calibration.",
            "anthropometric_too_few_frames":
                f"Very few usable frames ({frames_used}). "
                f"Population-average body proportions used. "
                f"Accuracy is significantly reduced — please reshoot.",
        }
        detail = friendly.get(fallback_reason, f"Calibration fallback: {fallback_reason}.")
        return _clamp(tier_score), detail

    # Complete failure (should not occur after our fixes, but kept as safety net)
    return 0.20, "Calibration failed entirely. Results are unreliable."


# ── Sub-score: Pose ───────────────────────────────────────────────────────────

def _pose_sub_score(
    pose_detection_rate: float,
    mean_landmark_visibility: float,
    frames_filtered_with_butterworth: int,
    total_frames: int,
) -> tuple[float, str]:
    """
    Compute S_pose and its human-readable explanation.

    Two factors:
        - Detection rate (0→1): what fraction of frames had a full pose.
        - Mean visibility (0→1): average landmark confidence across all frames.
    """
    # Butterworth coverage bonus: full filtering = +0.05
    filter_ratio = frames_filtered_with_butterworth / max(total_frames, 1)
    filter_bonus = 0.05 * filter_ratio

    # Base score: harmonic mean of detection rate and visibility
    # (harmonic mean penalises cases where one factor is very low)
    if pose_detection_rate + mean_landmark_visibility > 0:
        base = (2 * pose_detection_rate * mean_landmark_visibility /
                (pose_detection_rate + mean_landmark_visibility))
    else:
        base = 0.0

    score = _clamp(base + filter_bonus)

    if pose_detection_rate >= 0.95 and mean_landmark_visibility >= 0.85:
        detail = (
            f"Excellent pose quality: {pose_detection_rate:.0%} detection rate, "
            f"mean landmark confidence {mean_landmark_visibility:.0%}."
        )
    elif pose_detection_rate >= 0.80:
        detail = (
            f"Good pose quality: {pose_detection_rate:.0%} detection rate. "
            f"Ensure the full body is visible from the side for best results."
        )
    elif pose_detection_rate >= 0.60:
        detail = (
            f"Fair pose quality: {pose_detection_rate:.0%} detection rate. "
            f"Some frames were dropped due to occlusion or low confidence. "
            f"Joint angle estimates may be less precise."
        )
    else:
        detail = (
            f"Low pose quality: only {pose_detection_rate:.0%} of frames had a detected pose. "
            f"Ensure the player is filmed in a clear sagittal view with good lighting."
        )

    return score, detail


# ── Sub-score: Ball ───────────────────────────────────────────────────────────

def _ball_sub_score(
    ball_detection_rate: float,
    post_contact_detections: int,
    required_post_contact: int = 4,
) -> tuple[float, str]:
    """
    Compute S_ball and its human-readable explanation.

    Two factors:
        - Overall detection rate across the full clip.
        - Whether ≥ 4 post-contact detections are available for v0 estimation.
    """
    coverage_score = _clamp(ball_detection_rate)

    # Post-contact coverage: critical for v0. Scale from 0→1 as coverage 0→4 frames.
    post_ratio = _clamp(post_contact_detections / required_post_contact)
    # Post-contact is more important: weight it 60/40
    score = _clamp(0.40 * coverage_score + 0.60 * post_ratio)

    if post_contact_detections >= required_post_contact and ball_detection_rate >= 0.70:
        detail = (
            f"Ball detected in {ball_detection_rate:.0%} of frames. "
            f"{post_contact_detections} post-contact positions available — "
            f"speed estimation is reliable."
        )
    elif post_contact_detections >= required_post_contact:
        detail = (
            f"Ball detected in {ball_detection_rate:.0%} of frames overall. "
            f"Post-contact tracking sufficient ({post_contact_detections} frames). "
            f"Speed estimate is valid."
        )
    elif post_contact_detections >= 2:
        detail = (
            f"Only {post_contact_detections}/{required_post_contact} post-contact "
            f"ball positions detected. Speed estimate may be less accurate. "
            f"Ensure the ball is fully visible just after kick contact."
        )
    else:
        detail = (
            f"Ball not reliably detected after contact "
            f"({post_contact_detections} frames). "
            f"Ball speed cannot be estimated accurately. "
            f"Film from a fixed angle with the ball clearly visible."
        )

    return score, detail


# ── Summary generator ─────────────────────────────────────────────────────────

def _build_summary(overall: float, level: str, calib_detail: str) -> str:
    """
    Generate a single user-facing sentence describing overall confidence.
    """
    prefix = {
        "EXCELLENT": "Analysis confidence is excellent",
        "GOOD":      "Analysis confidence is good",
        "FAIR":      "Analysis confidence is fair",
        "LOW":       "Analysis confidence is low",
    }[level]

    if level in ("EXCELLENT", "GOOD"):
        return f"{prefix} ({overall:.0%}). Results are reliable."
    else:
        # Include the most limiting factor
        return (
            f"{prefix} ({overall:.0%}). "
            f"Key issue: {calib_detail.split('.')[0]}."
        )


# ── Public API ────────────────────────────────────────────────────────────────

def compute_confidence_score(
    # Calibration inputs
    gate_passed: bool,
    gate_passed_with_fallback: bool,
    fallback_reason: Optional[str],
    thigh_variation_m: float,
    thigh_tolerance_m: float,
    calib_frames_used: int,

    # Pose inputs
    pose_detection_rate: float,
    mean_landmark_visibility: float,
    frames_filtered_with_butterworth: int,
    total_analysis_frames: int,

    # Ball inputs
    ball_detection_rate: float,
    post_contact_detections: int,
) -> ConfidenceScore:
    """
    Compute the composite confidence score for one analysis result.

    Parameters
    ----------
    gate_passed : bool
        True if calibration strict gate passed.
    gate_passed_with_fallback : bool
        True if a fallback was used (relaxed or anthropometric).
    fallback_reason : str or None
        Key identifying which fallback was applied.
    thigh_variation_m : float
        Thigh segment variation over the calibration window [m].
    thigh_tolerance_m : float
        Allowed thigh variation threshold [m].
    calib_frames_used : int
        Number of valid calibration frames.
    pose_detection_rate : float ∈ [0, 1]
        Fraction of video frames with a detected pose.
    mean_landmark_visibility : float ∈ [0, 1]
        Mean MediaPipe landmark visibility across all detected frames.
    frames_filtered_with_butterworth : int
        Number of landmarks that had enough frames for Butterworth filtering.
    total_analysis_frames : int
        Total frames submitted for analysis.
    ball_detection_rate : float ∈ [0, 1]
        Fraction of frames where the ball was detected.
    post_contact_detections : int
        Number of ball detections available after the contact frame.

    Returns
    -------
    ConfidenceScore
    """
    s_calib, calib_detail = _calibration_sub_score(
        gate_passed, gate_passed_with_fallback, fallback_reason,
        thigh_variation_m, thigh_tolerance_m, calib_frames_used
    )
    s_pose, pose_detail = _pose_sub_score(
        pose_detection_rate, mean_landmark_visibility,
        frames_filtered_with_butterworth, total_analysis_frames
    )
    s_ball, ball_detail = _ball_sub_score(
        ball_detection_rate, post_contact_detections
    )

    overall = _clamp(_W_CALIB * s_calib + _W_POSE * s_pose + _W_BALL * s_ball)
    level   = _level(overall)
    summary = _build_summary(overall, level, calib_detail)

    logger.info(
        f"Confidence: overall={overall:.2f} ({level}) | "
        f"calib={s_calib:.2f} pose={s_pose:.2f} ball={s_ball:.2f}"
    )

    return ConfidenceScore(
        overall=round(overall, 3),
        level=level,
        calibration_score=round(s_calib, 3),
        pose_score=round(s_pose, 3),
        ball_score=round(s_ball, 3),
        calibration_detail=calib_detail,
        pose_detail=pose_detail,
        ball_detail=ball_detail,
        summary=summary,
    )


# ── Input quality validation ──────────────────────────────────────────────────

@dataclass
class InputQualityReport:
    """
    Pre-analysis quality report emitted by /process-video.
    Allows the Flutter UI to warn the user before they submit for analysis.
    """
    usable: bool                       # False = hard block; True = proceed (possibly with warnings)
    quality_level: str                 # GOOD | FAIR | POOR | UNUSABLE
    issues: list[str]                  # Machine-readable issue codes
    user_messages: list[str]           # Plain English, shown in the app
    suggestions: list[str]             # Actionable improvement hints


# Maps for user-facing messages
_ISSUE_MESSAGES: dict[str, str] = {
    "no_ball_detected":
        "The ball was not detected in this video.",
    "ball_detected_too_few_frames":
        "The ball was only detected in a small number of frames.",
    "low_pose_detection":
        "Pose could not be detected in many frames.",
    "very_low_pose_detection":
        "The player's body was barely visible — pose detection nearly failed.",
    "no_post_contact_ball":
        "The ball was not detected after foot contact — speed cannot be estimated.",
    "insufficient_post_contact_ball":
        "Too few ball positions detected after contact for reliable speed estimation.",
    "calibration_fallback_anthropometric":
        "Body measurements were estimated from population averages, not measured directly.",
    "calibration_failed":
        "Calibration failed completely — analysis cannot proceed.",
    "low_fps":
        "Video frame rate is lower than the recommended 60 fps.",
}

_ISSUE_SUGGESTIONS: dict[str, str] = {
    "no_ball_detected":
        "Use a high-contrast ball. Ensure the ball is fully in frame throughout the kick.",
    "ball_detected_too_few_frames":
        "Place the camera closer to the penalty spot. Avoid motion blur (use 60 fps).",
    "low_pose_detection":
        "Film from a fixed position, side-on. Wear fitted clothing. Avoid backlighting.",
    "very_low_pose_detection":
        "Ensure the full body is visible from head to toe in the sagittal (side) view.",
    "no_post_contact_ball":
        "Do not pan the camera after the kick. Keep the ball in frame for 0.5 s after contact.",
    "insufficient_post_contact_ball":
        "Ensure the ball is visible for at least 4 frames (≈ 0.07 s) after contact.",
    "calibration_fallback_anthropometric":
        "Stand still in T-pose for at least 2 seconds with all joints clearly visible.",
    "calibration_failed":
        "Repeat the calibration clip. Stand in T-pose, arms out, for 3 seconds.",
    "low_fps":
        "Set your smartphone to 60 fps (slow-motion or standard 60fps mode).",
}


def assess_input_quality(
    pose_detection_rate: float,
    ball_detection_rate: float,
    post_contact_detections: int,
    fps: float,
    calibration_gate_passed: bool,
    calibration_fallback_reason: Optional[str],
) -> InputQualityReport:
    """
    Assess the quality of the /process-video inputs and produce a
    structured report for the Flutter UI.

    Parameters
    ----------
    pose_detection_rate : float
        Fraction of frames with a detected pose ∈ [0, 1].
    ball_detection_rate : float
        Fraction of frames with a detected ball ∈ [0, 1].
    post_contact_detections : int
        Number of ball detections available after the contact frame.
    fps : float
        Detected video frame rate.
    calibration_gate_passed : bool
        Whether calibration strict or fallback gate passed.
    calibration_fallback_reason : str or None
        Calibration fallback tier used, if any.

    Returns
    -------
    InputQualityReport
    """
    issues: list[str] = []

    # ── Ball checks ──────────────────────────────────────────────────────────
    if ball_detection_rate == 0.0:
        issues.append("no_ball_detected")
    elif ball_detection_rate < 0.20:
        issues.append("ball_detected_too_few_frames")

    if post_contact_detections == 0:
        issues.append("no_post_contact_ball")
    elif post_contact_detections < 4:
        issues.append("insufficient_post_contact_ball")

    # ── Pose checks ──────────────────────────────────────────────────────────
    if pose_detection_rate < 0.40:
        issues.append("very_low_pose_detection")
    elif pose_detection_rate < 0.70:
        issues.append("low_pose_detection")

    # ── Calibration checks ───────────────────────────────────────────────────
    if not calibration_gate_passed:
        issues.append("calibration_failed")
    elif calibration_fallback_reason and "anthropometric" in calibration_fallback_reason:
        issues.append("calibration_fallback_anthropometric")

    # ── FPS check ────────────────────────────────────────────────────────────
    if fps < 25.0:
        issues.append("low_fps")

    # ── Determine overall quality ────────────────────────────────────────────
    # Hard blockers: conditions that make analysis impossible regardless
    # of other factors. Everything else is a degradation, not a block.
    hard_blockers = {
        "no_ball_detected",          # v0 estimation impossible
        "calibration_failed",        # no scale reference at all
        "very_low_pose_detection",   # IK cannot run without pose
    }
    has_blocker = any(i in hard_blockers for i in issues)
    n_issues = len(issues)

    if has_blocker:
        quality_level = "UNUSABLE"
        usable = False
    elif n_issues >= 4:
        quality_level = "UNUSABLE"
        usable = False
    elif n_issues >= 3:
        quality_level = "POOR"
        usable = True    # proceed with strong warnings
    elif n_issues >= 1:
        quality_level = "FAIR"
        usable = True
    else:
        quality_level = "GOOD"
        usable = True

    user_messages = [_ISSUE_MESSAGES[i] for i in issues if i in _ISSUE_MESSAGES]
    suggestions   = [_ISSUE_SUGGESTIONS[i] for i in issues if i in _ISSUE_SUGGESTIONS]

    logger.info(
        f"Input quality: {quality_level} | usable={usable} | "
        f"issues={issues}"
    )

    return InputQualityReport(
        usable=usable,
        quality_level=quality_level,
        issues=issues,
        user_messages=user_messages,
        suggestions=suggestions,
    )
