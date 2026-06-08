"""
Ball Detector — PenaltyIQ Backend
=====================================
Detects the FIFA soccer ball in video frames using OpenCV HoughCircles.

Design rationale [MODEL]:
    The FIFA ball (size 5) is a high-contrast, approximately circular
    object against the grass/pitch background.

    HoughCircles (Hough Transform for circles) detects circles in
    grayscale images without requiring a trained ML model.

    Advantages:
        - Zero additional model downloads (uses OpenCV already installed).
        - Deterministic output (no stochastic inference).
        - Real-time capable on CPU.

    Limitations [LIMIT]:
        - Sensitive to ball occlusion (by player limbs) near contact frame.
        - May fail if ball is motion-blurred at 60fps. [SPEC §6.3]
        - Works best with high-contrast balls on uniform pitch background.
        - For production: replace with YOLOv8-nano for robustness.

Ball size reference [FIFA-2024]:
    FIFA size 5 ball: circumference 68–70 cm → diameter ≈ 21.6–22.3 cm.
    We use d_ball = 0.22 m (specification midpoint). [SPEC §1.2.1]

Physical constraint used for filtering:
    If scale_m_per_px is known from calibration:
        Expected ball diameter in pixels = 0.22 / scale_m_per_px
        Filter detections: |detected_px - expected_px| / expected_px ≤ 0.15
    If scale is not yet known (pre-calibration):
        Accept any detection within [15px, 120px] diameter range.
        [MODEL]: Based on typical smartphone video at 1–4m distance.
"""

import cv2
import numpy as np
import logging
from dataclasses import dataclass
from typing import Optional

from constants.fifa_constants import BALL_DIAMETER_M

logger = logging.getLogger("penaltyiq.ball_detector")


# ── Detection parameters [MODEL] ──────────────────────────────────────────────

# HoughCircles dp parameter: inverse accumulator resolution.
# dp=1: accumulator has same resolution as input image.
HOUGH_DP: float = 1.2

# Minimum distance between circle centres [pixels].
# Prevents detecting the same ball multiple times.
HOUGH_MIN_DIST: int = 50

# Canny edge detector upper threshold (HoughCircles uses this internally).
HOUGH_PARAM1: int = 100

# Accumulator threshold for circle detection.
# Lower = more detections (including false positives).
# Higher = fewer detections (more precise).
HOUGH_PARAM2: int = 30

# Absolute radius range for detected circles [pixels].
# [MODEL]: Based on FIFA ball at 1–4m camera distance in smartphone video.
# At 1m distance: ball ≈ 120px diameter.
# At 4m distance: ball ≈ 30px diameter.
HOUGH_MIN_RADIUS: int = 12    # 24px diameter minimum
HOUGH_MAX_RADIUS: int = 70    # 140px diameter maximum

# Scale validation tolerance.
# If calibration scale is available, reject detections that deviate
# more than this fraction from the expected ball size. [MODEL]
SCALE_VALIDATION_TOLERANCE: float = 0.20   # ±20%


@dataclass
class BallDetection:
    """
    Detected ball in a single frame.

    Centre coordinates are in pixel space.
    diameter_px is used to compute the metric scale factor. [SPEC §1.2.1]
    """
    x_centre_px: float    # ball centre x [pixels]
    y_centre_px: float    # ball centre y [pixels]
    radius_px: float      # detected radius [pixels]
    diameter_px: float    # 2 × radius [pixels]
    confidence: float     # heuristic confidence ∈ [0, 1]


def preprocess_for_ball_detection(frame_bgr: np.ndarray) -> np.ndarray:
    """
    Preprocess a BGR frame for HoughCircles detection.

    Pipeline:
        1. Convert to grayscale (HoughCircles requires single channel).
        2. Apply Gaussian blur (reduces noise, improves circle detection).
        3. Optional: CLAHE for low-contrast frames.

    Parameters
    ----------
    frame_bgr : np.ndarray [H, W, 3]
        OpenCV BGR frame.

    Returns
    -------
    gray_blurred : np.ndarray [H, W]
        Preprocessed single-channel image.
    """
    # Convert to grayscale
    gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

    # Gaussian blur: kernel size 9×9, sigma=2.
    # [MODEL]: Kernel chosen to reduce JPEG compression artefacts
    # while preserving ball edge gradients.
    gray_blurred = cv2.GaussianBlur(gray, (9, 9), sigmaX=2.0)

    return gray_blurred


def detect_ball_in_frame(
    frame_bgr: np.ndarray,
    expected_diameter_px: Optional[float] = None
) -> Optional[BallDetection]:
    """
    Detect the soccer ball in a single frame using HoughCircles.

    Returns the best (most confident) ball detection, or None if
    no valid detection is found.

    Algorithm:
        1. Preprocess frame (grayscale + blur).
        2. Run HoughCircles with conservative parameters.
        3. Filter detections by radius range.
        4. If expected_diameter_px is known, filter by size consistency.
        5. Select the detection closest to expected size (or largest
           accumulator vote if no size reference).

    Parameters
    ----------
    frame_bgr : np.ndarray [H, W, 3]
        Single video frame.
    expected_diameter_px : float, optional
        Expected ball diameter in pixels from calibration scale.
        If provided, used to filter spurious detections.
        expected_diameter_px = BALL_DIAMETER_M / scale_m_per_px

    Returns
    -------
    BallDetection or None

    Notes
    -----
    [LIMIT]: HoughCircles may detect circular objects other than the ball
    (e.g., sponsor logos, corner flags). The size filter mitigates this.
    In production: YOLOv8-nano with class='sports ball' is more robust.
    """
    gray = preprocess_for_ball_detection(frame_bgr)
    h, w = gray.shape

    # Run HoughCircles
    circles = cv2.HoughCircles(
        gray,
        cv2.HOUGH_GRADIENT,
        dp=HOUGH_DP,
        minDist=HOUGH_MIN_DIST,
        param1=HOUGH_PARAM1,
        param2=HOUGH_PARAM2,
        minRadius=HOUGH_MIN_RADIUS,
        maxRadius=HOUGH_MAX_RADIUS,
    )

    if circles is None:
        logger.debug("HoughCircles: no circles detected.")
        return None

    # circles shape: (1, N, 3) → reshape to (N, 3)
    circles = np.round(circles[0]).astype(int)

    # Filter: remove circles whose centres are outside the frame
    valid_circles = [
        (x, y, r) for x, y, r in circles
        if 0 <= x < w and 0 <= y < h
    ]

    if not valid_circles:
        return None

    # Filter by expected size if calibration scale is available
    if expected_diameter_px is not None:
        expected_r = expected_diameter_px / 2.0
        filtered = [
            (x, y, r) for x, y, r in valid_circles
            if abs(r - expected_r) / expected_r <= SCALE_VALIDATION_TOLERANCE
        ]
        if filtered:
            valid_circles = filtered
        else:
            logger.debug(
                f"No circles within ±{SCALE_VALIDATION_TOLERANCE:.0%} "
                f"of expected radius {expected_r:.1f}px. "
                f"Using unfiltered detections."
            )

    if not valid_circles:
        return None

    # Select best detection: prefer circle closest to expected size
    if expected_diameter_px is not None:
        expected_r = expected_diameter_px / 2.0
        best = min(valid_circles, key=lambda c: abs(c[2] - expected_r))
    else:
        # Without size reference: prefer larger circles (more likely to be ball)
        best = max(valid_circles, key=lambda c: c[2])

    x, y, r = best
    diameter_px = float(2 * r)

    # Heuristic confidence: based on size match if reference available
    if expected_diameter_px is not None:
        size_error = abs(diameter_px - expected_diameter_px) / expected_diameter_px
        confidence = max(0.0, 1.0 - size_error / SCALE_VALIDATION_TOLERANCE)
    else:
        confidence = 0.7   # nominal confidence without size reference

    logger.debug(
        f"Ball detected: centre=({x},{y}), r={r}px, "
        f"d={diameter_px:.1f}px, confidence={confidence:.2f}"
    )

    return BallDetection(
        x_centre_px=float(x),
        y_centre_px=float(y),
        radius_px=float(r),
        diameter_px=diameter_px,
        confidence=confidence
    )


def extract_ball_detections_from_frames(
    frames_bgr: list[np.ndarray],
    scale_m_per_px: Optional[float] = None
) -> list[Optional[BallDetection]]:
    """
    Run ball detection on a list of frames.

    Parameters
    ----------
    frames_bgr : list of np.ndarray
        Ordered list of BGR video frames.
    scale_m_per_px : float, optional
        Calibrated scale factor. If provided, used to filter detections
        by expected ball size. [SPEC §1.2.1]

    Returns
    -------
    list of Optional[BallDetection]
        One entry per frame. None = no detection in that frame.
    """
    expected_d_px: Optional[float] = None
    if scale_m_per_px is not None and scale_m_per_px > 0:
        expected_d_px = BALL_DIAMETER_M / scale_m_per_px

    detections = []
    for i, frame in enumerate(frames_bgr):
        det = detect_ball_in_frame(frame, expected_d_px)
        detections.append(det)
        if det is not None:
            logger.debug(f"Frame {i}: ball at ({det.x_centre_px:.1f}, "
                        f"{det.y_centre_px:.1f})px, d={det.diameter_px:.1f}px")
        else:
            logger.debug(f"Frame {i}: no ball detected.")

    detected_count = sum(1 for d in detections if d is not None)
    logger.info(
        f"Ball detection complete: {detected_count}/{len(frames_bgr)} "
        f"frames with valid detection."
    )

    return detections


def extract_post_contact_ball_positions(
    detections: list[Optional[BallDetection]],
    contact_frame_index: int,
    n_intervals: int = 3
) -> list[tuple[float, float]]:
    """
    Extract ball centre pixel positions for v0 estimation.

    Returns the 4 consecutive ball positions starting from the
    contact frame, corresponding to [p1, p2, p3, p4] in [SPEC §2.4].

    Parameters
    ----------
    detections : list of Optional[BallDetection]
        All frame detections.
    contact_frame_index : int
        Index of the foot-ball contact frame.
        [MODEL]: Detected as the last frame where ball is stationary
        (low inter-frame displacement) before rapid displacement begins.
    n_intervals : int
        Number of frame intervals for v0 estimation. Default 3. [SPEC §2.4]

    Returns
    -------
    list of (x_px, y_px)
        Ball centre pixel coordinates for n_intervals+1 consecutive frames.

    Raises
    ------
    ValueError
        If insufficient detections are available after contact frame.
    """
    required_frames = n_intervals + 1  # need 4 positions for 3 intervals
    positions: list[tuple[float, float]] = []

    search_start = contact_frame_index
    search_end = min(contact_frame_index + required_frames * 3,
                     len(detections))

    for i in range(search_start, search_end):
        det = detections[i]
        if det is not None and det.confidence >= 0.5:
            positions.append((det.x_centre_px, det.y_centre_px))
            if len(positions) >= required_frames:
                break

    if len(positions) < required_frames:
        raise ValueError(
            f"Insufficient ball detections after contact frame "
            f"(frame {contact_frame_index}): "
            f"found {len(positions)}, need {required_frames}. "
            f"[SPEC §2.4]: v0 estimation requires 4 consecutive detections."
        )

    return positions[:required_frames]


def _median_filter_1d(values: list[float], kernel: int = 3) -> list[float]:
    """
    Apply a 1-D median filter to a list of floats.
    Edges are handled with reflection padding.
    [MODEL]: Removes single-frame jitter from tracking noise or
    compression artefacts without shifting the signal in time.
    """
    half = kernel // 2
    padded = [values[0]] * half + values + [values[-1]] * half
    return [
        float(np.median(padded[i:i + kernel]))
        for i in range(len(values))
    ]


def detect_contact_frame(
    detections: list[Optional[BallDetection]],
    fps: float = 60.0,
    pose_result: Optional["PoseVideoResult"] = None
) -> int:
    """
    Detect the foot-ball contact frame using velocity-derivative analysis.

    Algorithm [MODEL]:
        1. Compute inter-frame ball displacements (velocity proxy).
        2. Apply a 3-point median filter to remove single-frame jitter.
        3. Compute the first derivative (frame-to-frame acceleration).
        4. Contact frame = first frame where acceleration exceeds
           mean + 3σ of the pre-kick baseline (first 20% of frames).
        5. Validate: post-contact displacements must be monotonically
           increasing for ≥ 3 consecutive frames (true ball flight).
        6. Fallback A: original fixed-threshold method (5px/frame).
        7. Fallback B: frame of maximum displacement as last resort.

    Parameters
    ----------
    detections : list of Optional[BallDetection]
    fps : float — video frame rate

    Returns
    -------
    contact_frame_index : int
        Index of the estimated contact frame.

    Notes
    -----
    The statistical baseline adapts automatically to any FPS or
    camera distance — no hard-coded pixel threshold is the primary
    decision maker. [SPEC §2.4]
    """
    # ── Step 1: Build displacement series ─────────────────────────────────
    frame_indices: list[int] = []
    raw_disps: list[float] = []
    prev_pos: Optional[tuple[float, float]] = None

    for i, det in enumerate(detections):
        if det is None:
            prev_pos = None
            continue
        curr_pos = (det.x_centre_px, det.y_centre_px)
        if prev_pos is not None:
            dx = curr_pos[0] - prev_pos[0]
            dy = curr_pos[1] - prev_pos[1]
            raw_disps.append(float(np.sqrt(dx**2 + dy**2)))
            frame_indices.append(i)
        prev_pos = curr_pos

    if not raw_disps:
        logger.warning("No displacement data for contact frame detection.")
        return 0

    n = len(raw_disps)

    # ── Step 2: Smooth displacements ──────────────────────────────────────
    smooth_disps = _median_filter_1d(raw_disps, kernel=3)

    # ── Step 3: First derivative (acceleration) ───────────────────────────
    accel = [
        smooth_disps[i + 1] - smooth_disps[i]
        for i in range(n - 1)
    ]

    # ── Step 4: Statistical baseline from first 20% of displacement frames ─
    baseline_end = max(3, n // 5)
    baseline = smooth_disps[:baseline_end]
    baseline_mean = float(np.mean(baseline))
    baseline_std  = float(np.std(baseline)) if len(baseline) > 1 else 1.0
    accel_threshold = baseline_mean + 3.0 * baseline_std + 1.0  # +1px guard

    logger.debug(
        f"Contact detection baseline: mean={baseline_mean:.2f}px "
        f"std={baseline_std:.2f}px threshold={accel_threshold:.2f}px"
    )

    # ── Step 5: Candidate detection via acceleration spike ────────────────
    candidate: Optional[int] = None
    for j, acc in enumerate(accel):
        if acc >= accel_threshold:
            # frame_indices[j] is the frame *after* the jump;
            # contact is the frame before the jump starts.
            raw_contact = frame_indices[j] - 1

            # Validate: post-contact must show ≥ 3 monotonically growing disps
            post_start = j + 1
            post_disps = smooth_disps[post_start:post_start + 3]
            if len(post_disps) >= 3 and all(
                post_disps[k] <= post_disps[k + 1]
                for k in range(len(post_disps) - 1)
            ):
                candidate = max(0, raw_contact)
                logger.info(
                    f"Contact frame detected (velocity-derivative) at "
                    f"frame {candidate} "
                    f"(accel spike {acc:.1f}px at displacement frame {frame_indices[j]})"
                )
                return candidate
            else:
                logger.debug(
                    f"Accel spike at frame {frame_indices[j]} rejected: "
                    f"post-contact trajectory not monotonic."
                )

    # ── Fallback A: original fixed-threshold method ───────────────────────
    STATIONARY_THRESHOLD_PX: float = max(5.0, baseline_mean + 2.0 * baseline_std)
    logger.debug(
        f"Velocity-derivative method inconclusive. "
        f"Trying threshold fallback ({STATIONARY_THRESHOLD_PX:.1f}px)."
    )
    for j, disp in enumerate(smooth_disps):
        if disp >= STATIONARY_THRESHOLD_PX:
            contact_frame = max(0, frame_indices[j] - 1)
            logger.info(
                f"Contact frame detected (threshold fallback) at "
                f"frame {contact_frame} (disp={disp:.1f}px)"
            )
            return contact_frame

    # ── Fallback B: Kinematic Contact Detection (Knee Extension) ──────────
    # If ball detections are too sparse, we use the player's pose.
    if pose_result is not None and pose_result.frames:
        try:
            kinematic_frame = _fallback_kinematic_contact_detection(pose_result)
            if kinematic_frame is not None:
                logger.warning(
                    f"Ball-based contact detection failed. "
                    f"Used Kinematic fallback (knee extension): frame {kinematic_frame}."
                )
                return kinematic_frame
        except Exception as e:
            logger.error(f"Kinematic contact fallback failed: {e}")

    # ── Fallback C: frame of maximum displacement ─────────────────────────
    max_idx = int(np.argmax(smooth_disps))
    contact_frame = max(0, frame_indices[max_idx] - 1)
    logger.warning(
        f"No clear contact frame. "
        f"Using maximum-displacement fallback: frame {contact_frame}."
    )
    return contact_frame


def _fallback_kinematic_contact_detection(pose_result: "PoseVideoResult") -> Optional[int]:
    """
    Kinematic contact detection based on the kicking leg's knee angle.
    A penalty kick biomechanically requires:
      1. Backswing: Peak knee flexion (minimum included angle).
      2. Contact: Peak knee extension immediately following backswing.
    """
    import math

    def _knee_angle(hip, knee, ankle) -> float:
        BA = (hip.x_norm - knee.x_norm, hip.y_norm - knee.y_norm)
        BC = (ankle.x_norm - knee.x_norm, ankle.y_norm - knee.y_norm)
        cross = BA[0] * BC[1] - BA[1] * BC[0]
        dot = BA[0] * BC[0] + BA[1] * BC[1]
        if dot == 0.0 and cross == 0.0:
            return 180.0
        return abs(math.degrees(math.atan2(cross, dot)))

    left_knees = []
    right_knees = []
    valid_frames = []

    for f in pose_result.frames:
        lms = f.landmarks
        if ("LEFT_HIP" in lms and "LEFT_KNEE" in lms and "LEFT_ANKLE" in lms and 
            "RIGHT_HIP" in lms and "RIGHT_KNEE" in lms and "RIGHT_ANKLE" in lms):
            left_knees.append(_knee_angle(lms["LEFT_HIP"], lms["LEFT_KNEE"], lms["LEFT_ANKLE"]))
            right_knees.append(_knee_angle(lms["RIGHT_HIP"], lms["RIGHT_KNEE"], lms["RIGHT_ANKLE"]))
            valid_frames.append(f.frame_index)

    if len(valid_frames) < 10:
        return None

    # Identify kicking leg: the one with the smallest minimum angle (deepest backswing)
    if min(left_knees) < min(right_knees):
        kick_angles = left_knees
    else:
        kick_angles = right_knees

    # Look for the backswing in the second half of the video
    half_idx = len(kick_angles) // 2
    second_half = kick_angles[half_idx:]
    
    # Backswing = minimum knee included angle (most bent)
    backswing_local_idx = int(np.argmin(second_half))
    backswing_global_idx = half_idx + backswing_local_idx

    # Contact = maximum knee included angle (most straight) after backswing
    post_backswing = kick_angles[backswing_global_idx:]
    if not post_backswing:
        return None
        
    contact_local_idx = int(np.argmax(post_backswing))
    contact_global_idx = backswing_global_idx + contact_local_idx

    return valid_frames[contact_global_idx]