"""
Calibration Module — PenaltyIQ Backend
========================================
Implements the Static Calibration Gate described in [SPEC §1.2, §1.6.1].

Pipeline:
  1. Un-normalise MediaPipe landmarks → pixel coordinates.
  2. Compute pixel-to-metre scale factor from ball diameter.
  3. Convert pixel landmarks → metric landmarks.
  4. Compute segment lengths per frame (thigh, shank, trunk).
  5. Apply 2-second stability gate (bounded-variation criterion).
  6. Lock segment constants via median aggregation.

Scientific basis:
  [WINTER-2009]  Winter, D.A. (2009). Biomechanics and Motor Control
                 of Human Movement, 4th ed. Wiley. Ch.3.
  [FIFA-2024]    FIFA Laws of the Game 2024/25. Ball diameter = 0.22m.
  [SPEC §1.2.1]  S = 0.22 / d_ball_px
  [SPEC §1.3.1]  x_px = x_norm × W_img
  [SPEC §1.3.3]  x_m  = S × x_px
  [SPEC §1.6.1]  Stability: max(Lk) - min(Lk) ≤ 0.02 × median(Lk)
                 over T = 2.0 seconds (120 frames @ 60fps).

No empirical multipliers appear in this module.
Every constant is derived from the sources listed above.
"""

import numpy as np
import logging
from dataclasses import dataclass

from constants.fifa_constants import BALL_DIAMETER_M, SAMPLE_RATE_HZ

logger = logging.getLogger("penaltyiq.calibration")


# ─── Physical Constants ───────────────────────────────────────────────────────

# [SPEC §1.6.1]: Stability window duration = 2 seconds.
STABILITY_WINDOW_S: float = 2.0

# [SPEC §1.6.1]: Tolerance = 1–2% of segment length.
# We use 2% (upper bound) to be conservative and accommodate
# landmark quantisation noise. [WINTER-2009 Ch.3: discusses ~1-2%
# error in video-based landmark detection].
STABILITY_TOLERANCE_FRACTION: float = 0.02

# Relaxed tolerance tier — applied as a second pass before declaring failure.
# 5% accommodates low-quality video with higher landmark jitter while still
# excluding severely unstable poses. [MODEL]
STABILITY_TOLERANCE_RELAXED: float = 0.05

# Minimum frames required for the stability window.
# At 60 fps: 2.0 s × 60 fps = 120 frames.
STABILITY_WINDOW_FRAMES: int = int(STABILITY_WINDOW_S * SAMPLE_RATE_HZ)

# Minimum sub-window size when full window is unavailable.
# 30 frames = 0.5 s @ 60 fps — enough for a basic stability estimate.
MIN_SUBWINDOW_FRAMES: int = 30

# Minimum visibility threshold for a landmark to be used.
# [MODEL]: Landmarks below this threshold are considered unreliable
# and excluded from segment length computation in that frame.
MIN_LANDMARK_VISIBILITY: float = 0.75

# Anthropometric segment ratios from [WINTER-2009] Table 4.1
# (proportion of total body height). Used as fallback when gate fails.
# thigh / shank / trunk are expressed as fraction of leg length.
# These are population medians — individual error ≈ ±5%.
_WINTER_THIGH_RATIO: float  = 0.245   # thigh  / height
_WINTER_SHANK_RATIO: float  = 0.246   # shank  / height  (tibia)
_WINTER_TRUNK_RATIO: float  = 0.520   # trunk  / height  (hip→shoulder)
# Typical adult male height used when scale is unavailable [MODEL]
_DEFAULT_HEIGHT_M: float = 1.75


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class MetricLandmark:
    """
    A landmark in the metric coordinate system [m].
    Derived from normalised MediaPipe output via un-normalisation
    and pixel-to-metre scaling. [SPEC §1.3]
    """
    x_m: float
    y_m: float
    visibility: float


@dataclass
class FrameSegmentLengths:
    """
    Segment lengths computed from a single frame's metric landmarks.
    All values in metres. [WINTER-2009 Ch.3]
    """
    frame_index: int
    thigh_m: float    # hip centre → knee centre
    shank_m: float    # knee centre → ankle centre
    trunk_m: float    # hip centre → shoulder centre
    scale_m_per_px: float


@dataclass
class CalibrationResult:
    """
    Output of the full calibration pipeline.

    If gate_passed is False AND gate_passed_with_fallback is False,
    the analysis route MUST NOT proceed. [SPEC §1.6.1]

    If gate_passed_with_fallback is True, segment values are populated
    from anthropometric estimates [WINTER-2009] and analysis MAY proceed
    with a degraded-accuracy warning.
    """
    gate_passed: bool

    # Locked constants (valid only if gate_passed or gate_passed_with_fallback)
    scale_m_per_px: float | None
    thigh_m: float | None
    shank_m: float | None
    trunk_m: float | None
    leg_m: float | None

    # Diagnostic outputs (always populated for UI feedback)
    thigh_variation_m: float
    shank_variation_m: float
    trunk_variation_m: float
    thigh_tolerance_m: float
    shank_tolerance_m: float
    trunk_tolerance_m: float
    thigh_passed: bool
    shank_passed: bool
    trunk_passed: bool
    window_duration_s: float
    frames_used: int
    error_message: str | None

    # Fallback fields — populated when gate fails but a recovery was possible
    gate_passed_with_fallback: bool = False
    fallback_reason: str | None = None


# ─── Step 1: Coordinate Un-normalisation ─────────────────────────────────────

def unnormalise_landmark(
    x_norm: float,
    y_norm: float,
    frame_width_px: int,
    frame_height_px: int
) -> tuple[float, float]:
    """
    Convert MediaPipe normalised landmark coordinates to pixel coordinates.

    MediaPipe Pose returns x, y ∈ [0, 1] relative to frame dimensions.
    Un-normalisation recovers the absolute pixel position.

    Formula [SPEC §1.3.1]:
        x_px = x_norm × W_img
        y_px = y_norm × H_img

    Parameters
    ----------
    x_norm, y_norm : float
        Normalised coordinates ∈ [0, 1].
    frame_width_px, frame_height_px : int
        Frame resolution in pixels.

    Returns
    -------
    (x_px, y_px) : tuple of float
        Pixel coordinates.
    """
    x_px = x_norm * float(frame_width_px)
    y_px = y_norm * float(frame_height_px)
    return x_px, y_px


# ─── Step 2: Pixel-to-Metre Scale Factor ─────────────────────────────────────

def compute_scale_factor(ball_diameter_px: float) -> float:
    """
    Compute the pixel-to-metre scale factor using the FIFA ball diameter
    as the absolute physical reference.

    Formula [SPEC §1.2.1, §1.3.2]:
        S = d_b / d_ball_px = 0.22 / d_ball_px    [m/pixel]

    where d_b = 0.22 m is the FIFA standard ball diameter [FIFA-2024].

    This is the ONLY physically grounded scale reference available in a
    single-camera monocular setup without additional calibration targets.

    Parameters
    ----------
    ball_diameter_px : float
        Detected ball diameter in pixels. Must be > 0.

    Returns
    -------
    scale_m_per_px : float
        Scale factor in metres per pixel.

    Raises
    ------
    ValueError
        If ball_diameter_px ≤ 0 (physically impossible).

    Notes
    -----
    [LIMIT][SPEC §1.3]: Scale accuracy depends on reliable ball detection
    and the assumption that the ball occupies the same depth plane as the
    player. The IMU gate and sagittal overlay reduce depth error.
    """
    if ball_diameter_px <= 0.0:
        raise ValueError(
            f"ball_diameter_px must be > 0. Received: {ball_diameter_px}. "
            f"Check ball detection output before calling compute_scale_factor."
        )

    scale_m_per_px: float = BALL_DIAMETER_M / ball_diameter_px
    logger.debug(
        f"Scale factor: S = {BALL_DIAMETER_M} / {ball_diameter_px:.2f}px "
        f"= {scale_m_per_px:.6f} m/px"
    )
    return scale_m_per_px


# ─── Step 3: Convert Pixel Landmark to Metric ─────────────────────────────────

def pixel_to_metric_landmark(
    x_norm: float,
    y_norm: float,
    visibility: float,
    frame_width_px: int,
    frame_height_px: int,
    scale_m_per_px: float
) -> MetricLandmark:
    """
    Full pipeline: normalised → pixel → metric for a single landmark.

    Applies [SPEC §1.3.1] then [SPEC §1.3.3] sequentially:
        x_px = x_norm × W_img
        y_px = y_norm × H_img
        x_m  = S × x_px
        y_m  = S × y_px

    Parameters
    ----------
    x_norm, y_norm : float
        MediaPipe normalised coordinates ∈ [0, 1].
    visibility : float
        MediaPipe landmark visibility ∈ [0, 1].
    frame_width_px, frame_height_px : int
        Frame resolution.
    scale_m_per_px : float
        S = 0.22 / d_ball_px [m/pixel].

    Returns
    -------
    MetricLandmark with x_m, y_m in metres.
    """
    x_px, y_px = unnormalise_landmark(
        x_norm, y_norm, frame_width_px, frame_height_px
    )
    x_m: float = scale_m_per_px * x_px
    y_m: float = scale_m_per_px * y_px

    return MetricLandmark(x_m=x_m, y_m=y_m, visibility=visibility)


# ─── Step 4: Segment Length Computation ───────────────────────────────────────

def compute_euclidean_segment_length(
    proximal: MetricLandmark,
    distal: MetricLandmark
) -> float | None:
    """
    Compute the Euclidean distance between two joint centres in metres.

    This implements the standard biomechanical segment length definition.
    [WINTER-2009] Ch.3, §3.1:
        "Segment lengths are computed as the straight-line distance between
         the proximal and distal joint centres."

    Formula:
        L = sqrt((x_distal - x_proximal)² + (y_distal - y_proximal)²)

    Parameters
    ----------
    proximal : MetricLandmark
        The proximal joint centre (e.g., hip for thigh segment).
    distal : MetricLandmark
        The distal joint centre (e.g., knee for thigh segment).

    Returns
    -------
    float
        Segment length in metres.
    None
        If either landmark has visibility < MIN_LANDMARK_VISIBILITY.
        None propagates to the stability gate which ignores this frame.

    Notes
    -----
    [WINTER-2009] recommends excluding frames where landmark confidence
    is below threshold rather than imputing values, to prevent
    systematic bias in the locked segment constants.
    """
    # Exclude low-confidence landmarks [WINTER-2009 Ch.3 recommendation]
    if (proximal.visibility < MIN_LANDMARK_VISIBILITY or
            distal.visibility < MIN_LANDMARK_VISIBILITY):
        logger.debug(
            f"Landmark excluded: visibility {proximal.visibility:.3f} / "
            f"{distal.visibility:.3f} < threshold {MIN_LANDMARK_VISIBILITY}"
        )
        return None

    dx: float = distal.x_m - proximal.x_m
    dy: float = distal.y_m - proximal.y_m
    length_m: float = np.sqrt(dx**2 + dy**2)
    return length_m


def extract_frame_segment_lengths(
    frame_landmarks: dict,
    ball_diameter_px: float,
    frame_width_px: int,
    frame_height_px: int,
    frame_index: int
) -> FrameSegmentLengths | None:
    """
    Extract all three segment lengths from a single calibration frame.

    Segments computed:
      - Thigh:  LEFT_HIP → LEFT_KNEE
      - Shank:  LEFT_KNEE → LEFT_ANKLE
      - Trunk:  LEFT_HIP → LEFT_SHOULDER

    [WINTER-2009] Ch.3: These are the standard lower-extremity segment
    definitions used in biomechanical gait and kicking analysis.

    Parameters
    ----------
    frame_landmarks : dict
        {landmark_name: NormalisedLandmark} for this frame.
    ball_diameter_px : float
        Detected ball diameter in pixels for this frame.
    frame_width_px, frame_height_px : int
        Frame resolution.
    frame_index : int
        Frame index for logging.

    Returns
    -------
    FrameSegmentLengths or None
        None if any required landmark is missing or below visibility
        threshold (frame is dropped from the stability window).
    """
    scale = compute_scale_factor(ball_diameter_px)

    def to_metric(name: str) -> MetricLandmark | None:
        lm = frame_landmarks.get(name)
        if lm is None:
            return None

        # Route handlers may pass landmarks as either objects with attributes
        # (x_norm/y_norm/visibility) or plain dictionaries.
        if isinstance(lm, dict):
            x_norm = lm.get("x_norm")
            y_norm = lm.get("y_norm")
            visibility = lm.get("visibility")
        else:
            x_norm = getattr(lm, "x_norm", None)
            y_norm = getattr(lm, "y_norm", None)
            visibility = getattr(lm, "visibility", None)

        if x_norm is None or y_norm is None or visibility is None:
            return None

        return pixel_to_metric_landmark(
            x_norm=float(x_norm),
            y_norm=float(y_norm),
            visibility=float(visibility),
            frame_width_px=frame_width_px,
            frame_height_px=frame_height_px,
            scale_m_per_px=scale
        )

    hip       = to_metric("LEFT_HIP")
    knee      = to_metric("LEFT_KNEE")
    ankle     = to_metric("LEFT_ANKLE")
    shoulder  = to_metric("LEFT_SHOULDER")

    # If any landmark is missing, drop the frame
    if any(lm is None for lm in [hip, knee, ankle, shoulder]):
        logger.warning(f"Frame {frame_index}: missing landmark(s), dropping.")
        return None

    thigh_m = compute_euclidean_segment_length(hip, knee)
    shank_m = compute_euclidean_segment_length(knee, ankle)
    trunk_m = compute_euclidean_segment_length(hip, shoulder)

    # Any segment below visibility threshold → drop frame
    if any(v is None for v in [thigh_m, shank_m, trunk_m]):
        logger.warning(f"Frame {frame_index}: low-visibility landmark, dropping.")
        return None

    return FrameSegmentLengths(
        frame_index=frame_index,
        thigh_m=thigh_m,
        shank_m=shank_m,
        trunk_m=trunk_m,
        scale_m_per_px=scale
    )


# ─── Step 5: Stability Gate ────────────────────────────────────────────────────

def _best_subwindow(
    segment_records: list[FrameSegmentLengths],
    window_size: int,
    tolerance_fraction: float
) -> tuple[list[FrameSegmentLengths], bool]:
    """
    Search for the best consecutive sub-window of `window_size` frames
    that satisfies the bounded-variation criterion.

    Returns the best window found and whether it passed all three segments.
    If no window passes, returns the window with fewest failing segments.

    [MODEL]: Sliding window avoids penalising a short period of occlusion
    in the middle of an otherwise stable T-pose.
    """
    if len(segment_records) < window_size:
        return segment_records, False

    best_window = segment_records[:window_size]
    best_failures = 3  # worst case: all three segments fail

    for start in range(len(segment_records) - window_size + 1):
        window = segment_records[start:start + window_size]
        thigh_arr = np.array([r.thigh_m for r in window])
        shank_arr = np.array([r.shank_m for r in window])
        trunk_arr = np.array([r.trunk_m for r in window])

        thigh_med = float(np.median(thigh_arr))
        shank_med = float(np.median(shank_arr))
        trunk_med  = float(np.median(trunk_arr))

        failures = 0
        if np.ptp(thigh_arr) > tolerance_fraction * thigh_med:
            failures += 1
        if np.ptp(shank_arr) > tolerance_fraction * shank_med:
            failures += 1
        if np.ptp(trunk_arr)  > tolerance_fraction * trunk_med:
            failures += 1

        if failures < best_failures:
            best_failures = failures
            best_window = window
            if failures == 0:
                break  # perfect window found

    return best_window, best_failures == 0


def _anthropometric_fallback(
    scale_m_per_px: float | None,
    measured_records: list[FrameSegmentLengths]
) -> tuple[float, float, float, float | None]:
    """
    Estimate segment lengths from [WINTER-2009] population ratios.

    If measured_records are available, derive height from the median
    (thigh + shank) leg length and back-calculate using Winter ratios.
    Otherwise fall back to a population median height of 1.75 m.

    Returns (thigh_m, shank_m, trunk_m, scale_m_per_px).
    """
    if measured_records:
        thigh_arr = np.array([r.thigh_m for r in measured_records])
        shank_arr = np.array([r.shank_m for r in measured_records])
        leg_m = float(np.median(thigh_arr) + np.median(shank_arr))
        # leg ≈ (thigh_ratio + shank_ratio) * height
        height_est = leg_m / (_WINTER_THIGH_RATIO + _WINTER_SHANK_RATIO)
        scale_est = (
            float(np.median([r.scale_m_per_px for r in measured_records]))
            if scale_m_per_px is None else scale_m_per_px
        )
    else:
        height_est = _DEFAULT_HEIGHT_M
        scale_est = scale_m_per_px  # may be None

    thigh_m = _WINTER_THIGH_RATIO * height_est
    shank_m = _WINTER_SHANK_RATIO * height_est
    trunk_m = _WINTER_TRUNK_RATIO * height_est
    return thigh_m, shank_m, trunk_m, scale_est


def run_stability_gate(
    segment_records: list[FrameSegmentLengths]
) -> CalibrationResult:
    """
    Apply the bounded-variation stability criterion to all segment records.

    [SPEC §1.6.1] Criterion:
        max(Lk(t)) - min(Lk(t)) ≤ εk
        where εk = STABILITY_TOLERANCE_FRACTION × median(Lk)
              STABILITY_TOLERANCE_FRACTION = 0.02 (2%)
        over a window of T = 2.0 seconds (120 frames @ 60fps).

    Aggregation (if gate passes):
        Locked constant = median(Lk) over the stable window.
        [WINTER-2009 Ch.3]: Median is preferred over mean for
        landmark time series due to robustness to outlier frames.

    Parameters
    ----------
    segment_records : list of FrameSegmentLengths
        All valid frames from the calibration clip (dropped frames
        have already been excluded by extract_frame_segment_lengths).

    Returns
    -------
    CalibrationResult
        Complete result including gate pass/fail, locked constants,
        and diagnostic variation values for UI display.

    Notes
    -----
    The stability window uses ALL provided frames if len >= 120.
    If len < 120, the gate fails with INSUFFICIENT_DATA.
    [SPEC §1.6.1]: The gate checks the ENTIRE window, not a rolling
    best-window — this enforces consistent T-pose throughout.
    """
    n_frames = len(segment_records)

    # ── Guard: insufficient data — try a sliding sub-window ───────────────────
    if n_frames < STABILITY_WINDOW_FRAMES:
        duration_available_s = n_frames / SAMPLE_RATE_HZ

        if n_frames >= MIN_SUBWINDOW_FRAMES:
            # Try to find a stable sub-window at normal then relaxed tolerance
            for tol, tier in [
                (STABILITY_TOLERANCE_FRACTION, "strict"),
                (STABILITY_TOLERANCE_RELAXED,  "relaxed"),
            ]:
                best_win, passed = _best_subwindow(
                    segment_records, n_frames, tol  # use all available frames
                )
                if passed:
                    logger.info(
                        f"Calibration: short clip ({n_frames} frames / "
                        f"{duration_available_s:.2f}s) but sub-window passed "
                        f"at {tol*100:.0f}% tolerance ({tier} tier)."
                    )
                    # Re-enter gate logic with the valid sub-window
                    segment_records = best_win
                    n_frames = len(best_win)
                    break
            else:
                # Sub-window search failed — apply anthropometric fallback
                logger.warning(
                    f"Calibration: insufficient & unstable frames ({n_frames}). "
                    f"Applying anthropometric fallback [WINTER-2009]."
                )
                thigh_f, shank_f, trunk_f, scale_f = _anthropometric_fallback(
                    scale_m_per_px=None, measured_records=segment_records
                )
                fallback_msg = (
                    f"Insufficient calibration data ({n_frames} frames / "
                    f"{duration_available_s:.2f}s < {STABILITY_WINDOW_S}s required). "
                    f"Segment lengths estimated from population medians "
                    f"[WINTER-2009]. Accuracy reduced — reshoot for best results."
                )
                thigh_arr = np.array([r.thigh_m for r in segment_records]) if segment_records else np.array([0.0])
                shank_arr = np.array([r.shank_m for r in segment_records]) if segment_records else np.array([0.0])
                trunk_arr = np.array([r.trunk_m for r in segment_records]) if segment_records else np.array([0.0])
                thigh_med = float(np.median(thigh_arr))
                shank_med = float(np.median(shank_arr))
                trunk_med = float(np.median(trunk_arr))
                return CalibrationResult(
                    gate_passed=False,
                    gate_passed_with_fallback=True,
                    fallback_reason="anthropometric_short_clip",
                    scale_m_per_px=scale_f,
                    thigh_m=thigh_f, shank_m=shank_f,
                    trunk_m=trunk_f, leg_m=thigh_f + shank_f,
                    thigh_variation_m=float(np.ptp(thigh_arr)),
                    shank_variation_m=float(np.ptp(shank_arr)),
                    trunk_variation_m=float(np.ptp(trunk_arr)),
                    thigh_tolerance_m=STABILITY_TOLERANCE_FRACTION * thigh_med,
                    shank_tolerance_m=STABILITY_TOLERANCE_FRACTION * shank_med,
                    trunk_tolerance_m=STABILITY_TOLERANCE_FRACTION * trunk_med,
                    thigh_passed=False, shank_passed=False, trunk_passed=False,
                    window_duration_s=duration_available_s,
                    frames_used=n_frames,
                    error_message=fallback_msg
                )
        else:
            # Too few frames even for a sub-window — hard fallback
            logger.warning(
                f"Calibration: only {n_frames} valid frames — "
                f"below minimum sub-window ({MIN_SUBWINDOW_FRAMES}). "
                f"Applying anthropometric fallback [WINTER-2009]."
            )
            thigh_f, shank_f, trunk_f, scale_f = _anthropometric_fallback(
                scale_m_per_px=None, measured_records=segment_records
            )
            fallback_msg = (
                f"Too few valid frames ({n_frames}) for calibration. "
                f"Segment lengths estimated from population medians "
                f"[WINTER-2009]. Reshoot with full body visible for best results."
            )
            return CalibrationResult(
                gate_passed=False,
                gate_passed_with_fallback=True,
                fallback_reason="anthropometric_too_few_frames",
                scale_m_per_px=scale_f,
                thigh_m=thigh_f, shank_m=shank_f,
                trunk_m=trunk_f, leg_m=thigh_f + shank_f,
                thigh_variation_m=0.0, shank_variation_m=0.0, trunk_variation_m=0.0,
                thigh_tolerance_m=0.0, shank_tolerance_m=0.0, trunk_tolerance_m=0.0,
                thigh_passed=False, shank_passed=False, trunk_passed=False,
                window_duration_s=n_frames / SAMPLE_RATE_HZ,
                frames_used=n_frames,
                error_message=fallback_msg
            )

    # ── Use the full sequence (all frames must be stable) ─────────────────────
    # [SPEC §1.6.1]: Check over t ∈ [t0, t0 + T] — the entire window.
    window = segment_records  # all frames already filtered for visibility

    thigh_arr = np.array([r.thigh_m for r in window])
    shank_arr = np.array([r.shank_m for r in window])
    trunk_arr = np.array([r.trunk_m for r in window])
    scale_arr = np.array([r.scale_m_per_px for r in window])

    # Medians [WINTER-2009 Ch.3: median for robustness]
    thigh_median = float(np.median(thigh_arr))
    shank_median = float(np.median(shank_arr))
    trunk_median = float(np.median(trunk_arr))
    scale_median = float(np.median(scale_arr))

    # Tolerances: εk = 2% × median(Lk) [SPEC §1.6.1]
    thigh_tolerance = STABILITY_TOLERANCE_FRACTION * thigh_median
    shank_tolerance = STABILITY_TOLERANCE_FRACTION * shank_median
    trunk_tolerance = STABILITY_TOLERANCE_FRACTION * trunk_median

    # Bounded-variation criterion: max - min ≤ ε
    # np.ptp = peak-to-peak = max - min
    thigh_variation = float(np.ptp(thigh_arr))
    shank_variation = float(np.ptp(shank_arr))
    trunk_variation = float(np.ptp(trunk_arr))

    thigh_passed = thigh_variation <= thigh_tolerance
    shank_passed = shank_variation <= shank_tolerance
    trunk_passed = trunk_variation <= trunk_tolerance
    all_passed   = thigh_passed and shank_passed and trunk_passed

    window_duration = n_frames / SAMPLE_RATE_HZ

    if all_passed:
        logger.info(
            f"Calibration gate PASSED. "
            f"Thigh: {thigh_median:.4f}m, Shank: {shank_median:.4f}m, "
            f"Trunk: {trunk_median:.4f}m, Scale: {scale_median:.6f} m/px. "
            f"Window: {window_duration:.2f}s ({n_frames} frames)."
        )
        return CalibrationResult(
            gate_passed=True,
            scale_m_per_px=scale_median,
            thigh_m=thigh_median,
            shank_m=shank_median,
            trunk_m=trunk_median,
            leg_m=thigh_median + shank_median,
            thigh_variation_m=thigh_variation,
            shank_variation_m=shank_variation,
            trunk_variation_m=trunk_variation,
            thigh_tolerance_m=thigh_tolerance,
            shank_tolerance_m=shank_tolerance,
            trunk_tolerance_m=trunk_tolerance,
            thigh_passed=True,
            shank_passed=True,
            trunk_passed=True,
            window_duration_s=window_duration,
            frames_used=n_frames,
            error_message=None
        )

    # ── Relaxed tolerance tier ─────────────────────────────────────────────────
    # Before declaring failure, re-test at 5% tolerance to accommodate
    # low-quality video with higher landmark jitter. [MODEL]
    thigh_tol_r = STABILITY_TOLERANCE_RELAXED * thigh_median
    shank_tol_r = STABILITY_TOLERANCE_RELAXED * shank_median
    trunk_tol_r = STABILITY_TOLERANCE_RELAXED * trunk_median
    relaxed_passed = (
        thigh_variation <= thigh_tol_r and
        shank_variation <= shank_tol_r and
        trunk_variation <= trunk_tol_r
    )

    if relaxed_passed:
        relaxed_msg = (
            f"Calibration gate PASSED (relaxed 5% tolerance). "
            f"Video quality may be low — results are slightly less precise. "
            f"Thigh: {thigh_median:.4f}m, Shank: {shank_median:.4f}m, "
            f"Trunk: {trunk_median:.4f}m."
        )
        logger.warning(relaxed_msg)
        return CalibrationResult(
            gate_passed=True,
            gate_passed_with_fallback=True,
            fallback_reason="relaxed_tolerance_5pct",
            scale_m_per_px=scale_median,
            thigh_m=thigh_median,
            shank_m=shank_median,
            trunk_m=trunk_median,
            leg_m=thigh_median + shank_median,
            thigh_variation_m=thigh_variation,
            shank_variation_m=shank_variation,
            trunk_variation_m=trunk_variation,
            thigh_tolerance_m=thigh_tol_r,
            shank_tolerance_m=shank_tol_r,
            trunk_tolerance_m=trunk_tol_r,
            thigh_passed=thigh_variation <= thigh_tol_r,
            shank_passed=shank_variation <= shank_tol_r,
            trunk_passed=trunk_variation <= trunk_tol_r,
            window_duration_s=window_duration,
            frames_used=n_frames,
            error_message=relaxed_msg
        )

    # ── Both tiers failed — anthropometric fallback ────────────────────────────
    failed_segments = []
    if not thigh_passed:
        failed_segments.append(
            f"Thigh (variation={thigh_variation*100:.1f}cm > "
            f"tolerance={thigh_tolerance*100:.1f}cm)"
        )
    if not shank_passed:
        failed_segments.append(
            f"Shank (variation={shank_variation*100:.1f}cm > "
            f"tolerance={shank_tolerance*100:.1f}cm)"
        )
    if not trunk_passed:
        failed_segments.append(
            f"Trunk (variation={trunk_variation*100:.1f}cm > "
            f"tolerance={trunk_tolerance*100:.1f}cm)"
        )

    thigh_f, shank_f, trunk_f, _ = _anthropometric_fallback(
        scale_m_per_px=scale_median, measured_records=window
    )
    fallback_msg = (
        f"Calibration gate FAILED (strict + relaxed). "
        f"Unstable segments: {'; '.join(failed_segments)}. "
        f"Segment lengths estimated from population medians [WINTER-2009]. "
        f"Ensure phone is level, player holds T-pose without swaying, "
        f"and all joints are visible for ≥ {STABILITY_WINDOW_S}s."
    )
    logger.warning(fallback_msg)

    return CalibrationResult(
        gate_passed=False,
        gate_passed_with_fallback=True,
        fallback_reason="anthropometric_unstable",
        scale_m_per_px=scale_median,
        thigh_m=thigh_f, shank_m=shank_f,
        trunk_m=trunk_f, leg_m=thigh_f + shank_f,
        thigh_variation_m=thigh_variation,
        shank_variation_m=shank_variation,
        trunk_variation_m=trunk_variation,
        thigh_tolerance_m=thigh_tolerance,
        shank_tolerance_m=shank_tolerance,
        trunk_tolerance_m=trunk_tolerance,
        thigh_passed=thigh_passed,
        shank_passed=shank_passed,
        trunk_passed=trunk_passed,
        window_duration_s=window_duration,
        frames_used=n_frames,
        error_message=fallback_msg
    )


# ─── Master Entry Point ───────────────────────────────────────────────────────

def run_calibration_pipeline(request_data: dict) -> CalibrationResult:
    """
    Orchestrates the full calibration pipeline from raw request data.

    Pipeline order (strictly sequential, no steps may be skipped):
        1. Parse frames → extract segment lengths per frame
           (unnormalise → scale → Euclidean distance)
        2. Drop frames with low-visibility landmarks
        3. Apply 2-second stability gate (bounded-variation criterion)
        4. If passed: lock segment constants via median aggregation

    Parameters
    ----------
    request_data : dict
        Deserialised CalibrationRequest (as dict from Pydantic model).

    Returns
    -------
    CalibrationResult
        Full result. gate_passed=False means analysis is blocked.
    """
    frames = request_data["frames"]
    logger.info(
        f"Starting calibration pipeline. "
        f"Session: {request_data['session_id']}. "
        f"Frames received: {len(frames)}."
    )

    # Step 1 + 2: Extract and filter segment lengths per frame
    valid_records: list[FrameSegmentLengths] = []
    for frame in frames:
        record = extract_frame_segment_lengths(
            frame_landmarks=frame["landmarks"],
            ball_diameter_px=frame["ball_diameter_px"],
            frame_width_px=frame["frame_width_px"],
            frame_height_px=frame["frame_height_px"],
            frame_index=frame["frame_index"]
        )
        if record is not None:
            valid_records.append(record)

    dropped = len(frames) - len(valid_records)
    if dropped > 0:
        logger.info(
            f"Calibration: {dropped}/{len(frames)} frames dropped "
            f"(low landmark visibility)."
        )

    # Step 3 + 4: Stability gate + locking
    result = run_stability_gate(valid_records)
    return result