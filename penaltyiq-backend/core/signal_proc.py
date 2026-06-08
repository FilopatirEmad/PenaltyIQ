# core/signal_proc.py
"""
Signal Processing Module — PenaltyIQ Backend  (Refactored v2)
==============================================================
Implements a 4th-Order Butterworth Low-Pass Filter for landmark
coordinate smoothing, operating in PIXEL SPACE.

Changes vs v1
-------------
* Filter order upgraded from 2 → 4.
  Rationale: A 4th-order Butterworth has a steeper roll-off
  (−80 dB/decade vs −40 dB/decade for order 2) while retaining
  a maximally flat passband.  This better suppresses the MediaPipe
  jitter band (10–30 Hz) without distorting the kick kinematics
  band (< 5 Hz).  Sports2D uses order 4 by default [Pagnon 2023].
* Input is now expected to be PIXEL coordinates (x_px, y_px), not
  normalised coordinates.  The conversion from normalised → pixel
  happens in angle_calculator._px_point() before the filter is
  applied to stored trajectories.
* MIN_SAMPLES guard lowered to 13 (mathematical minimum for
  4th-order sosfiltfilt: 2 × max_len(sos) + 1 = 2×4+1 = 9; we
  use 13 for a small safety margin), with a separate CLINICAL_MIN
  constant that triggers a WARNING (not ValueError) at 120 samples.

Scientific basis
----------------
Winter, D.A. (2009). Biomechanics and Motor Control of Human Movement
  (4th ed.). Wiley. Chapter 3, §3.2.
[SPEC] §1.4: cutoff 6 Hz, 30 fps.
Sports2D (Pagnon 2023): default Butterworth order = 4, cutoff = 6 Hz.

Design rationale (documented, not assumed)
------------------------------------------
Order 4   : Steeper roll-off than order 2; still maximally flat in
            passband.  Recommended by Sports2D for sports kinematics.
Cutoff 6 Hz: Preserves kicking kinematics (dominant energy < 5 Hz)
            while attenuating pose-estimation jitter (> 10 Hz).
            Winter (2009) §3.2: limb motion PSD peaks below 5 Hz.
sosfiltfilt: Zero-phase — prevents temporal shift of contact frame.
            Critical for contact-event timing accuracy.
SOS repr.  : Numerically stable cascade form (vs. transfer function).
"""

import logging
from typing import Sequence

import numpy as np
from scipy.signal import butter, sosfiltfilt

logger = logging.getLogger(__name__)

# ─── Filter Constants ────────────────────────────────────────────────────────

SAMPLE_RATE_HZ: float  = 30.0        # [SPEC §1.1] — 30 fps smartphone video
CUTOFF_HZ: float       = 6.0         # [SPEC §1.4.1] — Winter 2009 / Sports2D
FILTER_ORDER: int      = 4           # Upgraded from 2 → 4  [Sports2D default]
NYQUIST_HZ: float      = SAMPLE_RATE_HZ / 2.0       # 15.0 Hz
NORMALIZED_CUTOFF: float = CUTOFF_HZ / NYQUIST_HZ   # 0.4 — dimensionless

# Minimum samples for mathematically stable sosfiltfilt with order-4 filter.
# Formula: padlen = 3 × max(len(section)) = 3 × 4 = 12 → use 13 as guard.
MIN_SAMPLES: int      = 13
# Clinical grade: 2 seconds × 30 fps = 60 samples.
# Below this a WARNING is emitted but filtering still proceeds.
CLINICAL_MIN_SAMPLES: int = 60


def _build_filter_sos() -> np.ndarray:
    """
    Construct the 4th-order Butterworth SOS filter at 6 Hz / 30 fps.

    Returns
    -------
    sos : np.ndarray, shape (n_sections, 6)
        Second-order sections array for sosfiltfilt.
    """
    sos = butter(
        N=FILTER_ORDER,
        Wn=NORMALIZED_CUTOFF,
        btype="low",
        analog=False,
        output="sos",
    )
    return sos


def _build_filter_sos_adaptive(detected_fps: float) -> np.ndarray:
    """
    Build a filter SOS adapted to a non-standard frame rate.

    Used when the video is not 30 fps.  The cutoff stays at 6 Hz but
    the Nyquist frequency changes with the frame rate.

    Parameters
    ----------
    detected_fps : float — actual video frame rate (e.g. 60.0, 120.0).

    Returns
    -------
    sos : np.ndarray
    """
    nyquist   = detected_fps / 2.0
    norm_cut  = min(CUTOFF_HZ / nyquist, 0.99)   # clamp below 1.0
    sos = butter(N=FILTER_ORDER, Wn=norm_cut, btype="low", analog=False, output="sos")
    return sos


# Module-level singleton for the standard 30 fps filter (stateless).
_FILTER_SOS: np.ndarray = _build_filter_sos()


def apply_butterworth_filter(
    signal: Sequence[float],
    detected_fps: float = SAMPLE_RATE_HZ,
) -> np.ndarray:
    """
    Apply the 4th-order Butterworth low-pass filter (6 Hz) to a 1-D series.

    Parameters
    ----------
    signal : array-like of float
        Raw landmark coordinate time series **in pixel units** (x_px or y_px).
    detected_fps : float, optional
        Actual frame rate of the video.  Defaults to 30.0 fps.
        When != 30.0 an adaptive filter is built automatically.

    Returns
    -------
    filtered : np.ndarray — zero-phase filtered signal, same length as input.

    Raises
    ------
    ValueError
        If signal length < MIN_SAMPLES (13 frames).
        Mathematically insufficient for stable sosfiltfilt padding.

    Notes
    -----
    Below CLINICAL_MIN_SAMPLES (60 frames / 2 s) a WARNING is logged
    but filtering proceeds normally.  For reliable coaching feedback,
    at least 2 seconds of footage is recommended.
    """
    arr = np.asarray(signal, dtype=np.float64)

    if len(arr) < MIN_SAMPLES:
        raise ValueError(
            f"Signal length {len(arr)} is below the mathematical minimum "
            f"{MIN_SAMPLES} samples for stable 4th-order Butterworth filtering. "
            f"Ensure at least {MIN_SAMPLES / detected_fps:.2f}s of video data."
        )

    if len(arr) < CLINICAL_MIN_SAMPLES:
        logger.warning(
            "Signal length %d < clinical minimum %d (2 s @ 30 fps). "
            "Filtering proceeds but angle precision may be reduced. "
            "[SPEC §1.4 / Winter 2009 §3.2]",
            len(arr), CLINICAL_MIN_SAMPLES,
        )

    # Select filter: use singleton when fps matches default, else adaptive.
    if abs(detected_fps - SAMPLE_RATE_HZ) < 0.5:
        sos = _FILTER_SOS
    else:
        sos = _build_filter_sos_adaptive(detected_fps)
        logger.debug(
            "Using adaptive filter for fps=%.1f (cutoff %.1f Hz).",
            detected_fps, CUTOFF_HZ,
        )

    return sosfiltfilt(sos, arr)


def filter_landmark_trajectory(
    x_raw: Sequence[float],
    y_raw: Sequence[float],
    detected_fps: float = SAMPLE_RATE_HZ,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Filter the x and y coordinate trajectories of a single landmark.

    Per Winter (2009) §3.2: each coordinate axis is filtered independently.
    Angles are computed from filtered coordinates, NOT from raw coordinates.

    Parameters
    ----------
    x_raw, y_raw : array-like — raw coordinate time series (pixel units).
    detected_fps : float — actual video frame rate.

    Returns
    -------
    x_filtered, y_filtered : np.ndarray
    """
    x_filtered = apply_butterworth_filter(x_raw, detected_fps)
    y_filtered = apply_butterworth_filter(y_raw, detected_fps)
    return x_filtered, y_filtered


def filter_all_landmarks(
    landmark_trajectories: dict[str, dict[str, list[float]]],
    detected_fps: float = SAMPLE_RATE_HZ,
) -> dict[str, dict[str, np.ndarray]]:
    """
    Filter all landmark trajectories in a session.

    IMPORTANT: Input coordinates are expected to be in PIXEL UNITS
    (x multiplied by frame_width, y multiplied by frame_height) before
    calling this function.  This ensures the filter operates on physically
    meaningful units and that subsequent angle calculations are performed
    in pixel space (eliminating aspect-ratio distortion).

    Parameters
    ----------
    landmark_trajectories : dict
        Structure: {landmark_name: {"x": [...], "y": [...]}}
        Coordinates must be in PIXEL UNITS, not normalised [0, 1].
    detected_fps : float — actual video frame rate (default 30 fps).

    Returns
    -------
    filtered : dict — same structure with filtered np.ndarray values.

    Notes
    -----
    This is the primary entry point called by the analysis pipeline.
    All downstream joint angle calculations MUST use this output,
    never the raw input.  [WINTER-2009 §3.2, SPEC §1.4.1]
    """
    filtered: dict[str, dict[str, np.ndarray]] = {}
    for landmark_name, coords in landmark_trajectories.items():
        x_f, y_f = filter_landmark_trajectory(
            coords["x"], coords["y"], detected_fps
        )
        filtered[landmark_name] = {"x": x_f, "y": y_f}
    return filtered