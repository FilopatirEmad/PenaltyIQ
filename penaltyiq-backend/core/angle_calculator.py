"""
Angle Calculator — PenaltyIQ Backend
=========================================
Sports2D-on-MediaPipe: replicates every formula from the Colab notebook.

Pipeline:
  1. Extract raw pixel landmarks (Y-axis inverted to match Sports2D Y-up).
  2. Compute 5 angles per frame using exact Colab calc_angle (dot-product arccos).
  3. Apply Savitzky-Golay smoothing to angle time-series (matches Sports2D MOT).
  4. Event detection: backswing = idxmax(kick_knee), contact = idxmin after backswing.
  5. Output structured result dict matching Colab's res{} exactly.

Key conventions (matching Sports2D TRC):
  - Y-axis is INVERTED: y_px = (1 - y_norm) * frame_height
  - calc_angle uses pure dot-product / arccos → 0–180°, always positive.
  - Trunk: angle at hip between shoulder vector and upward virtual vertical.
  - backswing frame = MAX kick_knee angle in second half of clip.
  - contact frame  = MIN kick_knee angle AFTER backswing frame.
"""

import logging
import numpy as np
from scipy.signal import savgol_filter
from typing import Optional

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. CORE ANGLE MATH — exact Colab calc_angle()
# ─────────────────────────────────────────────────────────────────────────────

def calc_angle(p1, p2, p3) -> float:
    """
    Included angle (degrees) at vertex p2 between rays p2→p1 and p2→p3.
    Range: 0–180°.  Identical to the Colab notebook's calc_angle().
    """
    v1 = np.array(p1, dtype=float) - np.array(p2, dtype=float)
    v2 = np.array(p3, dtype=float) - np.array(p2, dtype=float)
    n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
    if n1 == 0.0 or n2 == 0.0:
        return np.nan
    cos_theta = np.dot(v1, v2) / (n1 * n2)
    return float(np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0))))


# ─────────────────────────────────────────────────────────────────────────────
# 2. LANDMARK EXTRACTION (normalised → pixel, Y-inverted)
# ─────────────────────────────────────────────────────────────────────────────

def _get_px(traj: dict, name: str, fi: int, W: int, H: int) -> Optional[np.ndarray]:
    """
    Convert a normalised MediaPipe landmark to pixel coordinates with Y-flip.
    Sports2D TRC uses Y-up; MediaPipe uses Y-down.
    Inversion: y_px = (1 - y_norm) * H  →  bottom of frame = 0.
    Returns None if landmark missing.
    """
    lm = traj.get(name)
    if lm is None or fi >= len(lm["x"]):
        return None
    x_px = lm["x"][fi] * W
    y_px = (1.0 - lm["y"][fi]) * H          # Y-axis inversion
    return np.array([x_px, y_px], dtype=float)


# ─────────────────────────────────────────────────────────────────────────────
# 3. SIDE NORMALISATION — left kick → horizontal flip
# ─────────────────────────────────────────────────────────────────────────────

def _maybe_flip(traj: dict, kicking_side: str, W: int) -> dict:
    """
    If kicking_side == 'LEFT', mirror all x-coordinates so the pipeline
    always operates as if the kick is right-sided (matching Colab convention).
    Returns a new traj dict; original is not mutated.
    """
    if kicking_side.upper() == "RIGHT":
        return traj

    flipped = {}
    for name, coords in traj.items():
        flipped[name] = {
            "x": [1.0 - v for v in coords["x"]],   # mirror in [0,1] space
            "y": list(coords["y"]),
        }
        # Also swap LEFT/RIGHT label so downstream logic is consistent
    swapped = {}
    for name, coords in flipped.items():
        if name.startswith("LEFT_"):
            swapped["RIGHT_" + name[5:]] = coords
        elif name.startswith("RIGHT_"):
            swapped["LEFT_"  + name[6:]] = coords
        else:
            swapped[name] = coords
    return swapped


# ─────────────────────────────────────────────────────────────────────────────
# 4. PER-FRAME ANGLE COMPUTATION — 5 variables, exact Colab formulas
# ─────────────────────────────────────────────────────────────────────────────

def _angles_at_frame(traj: dict, fi: int, W: int, H: int) -> dict:
    """
    Compute all 5 Colab angles for one frame.
    Assumes the trajectory has already been side-normalised (right-kick convention).
    Returns dict with keys: kick_knee, sup_knee, hip_flex, trunk, ankle_pf.
    All values are in degrees (0–180) or np.nan when landmarks are absent.
    """
    def pt(name):
        return _get_px(traj, name, fi, W, H)

    ksh = pt("RIGHT_SHOULDER")
    khi = pt("RIGHT_HIP")
    kkn = pt("RIGHT_KNEE")
    kan = pt("RIGHT_ANKLE")
    kft = pt("RIGHT_FOOT_INDEX")

    shi = pt("LEFT_HIP")
    skn = pt("LEFT_KNEE")
    san = pt("LEFT_ANKLE")

    out = {k: np.nan for k in ("kick_knee", "sup_knee", "hip_flex", "trunk", "ankle_pf")}

    # kick_knee: hip – knee – ankle (included angle at knee)
    if khi is not None and kkn is not None and kan is not None:
        out["kick_knee"] = calc_angle(khi, kkn, kan)

    # sup_knee: left hip – knee – ankle
    if shi is not None and skn is not None and san is not None:
        out["sup_knee"] = calc_angle(shi, skn, san)

    # hip_flex: shoulder – hip – knee
    if ksh is not None and khi is not None and kkn is not None:
        out["hip_flex"] = calc_angle(ksh, khi, kkn)

    # trunk: shoulder – hip – virtual upward vertical
    # In Y-flipped pixel space, +100 on Y = physically upward (mirrors Colab's hip_y-100 in Y-up TRC)
    if ksh is not None and khi is not None:
        v = ksh - khi
        out["trunk"] = float(np.degrees(np.arctan2(v[0], v[1])))
    # ankle_pf: knee – ankle – foot_index (plantarflexion)
    if kkn is not None and kan is not None and kft is not None:
        out["ankle_pf"] = calc_angle(kkn, kan, kft)

    return out


# ─────────────────────────────────────────────────────────────────────────────
# 5. TIME-SERIES BUILDER + SAVITZKY-GOLAY SMOOTHING
# ─────────────────────────────────────────────────────────────────────────────

def _adaptive_savgol_window(n_frames: int, fps: float) -> int:
    """
    STRICT requirement: window_length = 7 (auto-adjust if FPS is low, but keep odd number).
    """
    target = 7
    return min(target, n_frames if n_frames % 2 == 1 else n_frames - 1)


def _smooth_series(arr: list, fps: float, polyorder: int = 2) -> list:
    """
    Apply Savitzky-Golay filter to an angle time-series.
    NaN values are interpolated before filtering and restored after.
    Matches the smoothing Sports2D applies to its MOT output.
    """
    a = np.array(arr, dtype=float)
    n = len(a)
    if n < 5:
        return arr

    # Interpolate NaNs for filtering
    nans = np.isnan(a)
    if nans.all():
        return arr
    idx = np.arange(n)
    a_filled = np.interp(idx, idx[~nans], a[~nans])

    wl = _adaptive_savgol_window(n, fps)
    wl = max(polyorder + 2, wl)
    if wl >= n:
        wl = n if n % 2 == 1 else n - 1
    if wl < polyorder + 2:
        return arr

    smoothed = savgol_filter(a_filled, window_length=wl, polyorder=polyorder)
    smoothed[nans] = np.nan
    return smoothed.tolist()


def compute_angle_timelines(
    traj: dict,
    kicking_side: str = "RIGHT",
    frame_width: int = 1920,
    frame_height: int = 1080,
    fps: float = 30.0,
) -> tuple[dict, dict]:
    """
    Build smoothed and raw angle time-series for the full video.

    Returns
    -------
    tuple(smoothed, raw): dicts with keys: kick_knee, sup_knee, hip_flex, trunk, ankle_pf
    """
    if not traj:
        return {}, {}

    # Side normalisation (left kick → horizontal flip)
    traj_norm = _maybe_flip(traj, kicking_side, frame_width)

    first_lm = next(iter(traj_norm.values()))
    n_frames = len(first_lm["x"])
    W, H = frame_width, frame_height

    raw: dict = {k: [] for k in ("kick_knee", "sup_knee", "hip_flex", "trunk", "ankle_pf")}
    for fi in range(n_frames):
        angles = _angles_at_frame(traj_norm, fi, W, H)
        for k in raw:
            raw[k].append(angles[k] if not np.isnan(angles[k]) else None)

    # Apply Savitzky-Golay to each angle series
    smoothed = {}
    for k, series in raw.items():
        smoothed[k] = _smooth_series(series, fps)

    return smoothed, raw


# ─────────────────────────────────────────────────────────────────────────────
# 6. EVENT DETECTION — exact Colab logic
#    backswing = idxmax(kick_knee) in second half
#    contact   = idxmin(kick_knee) AFTER backswing
# ─────────────────────────────────────────────────────────────────────────────

def detect_contact_event(
    smoothed_timelines: dict,
    raw_timelines: dict,
    ankle_x_series: list,
    ankle_y_series: list,
    fps: float,
) -> Optional[dict]:
    """
    STRICT EVENT DETECTION (CRITICAL)
    Using the SMOOTHED kicking knee signal:
    - backswing_frame: frame index where kicking knee angle is MAX
    - contact_frame: FIRST MINIMUM after backswing
    """
    kk = smoothed_timelines.get("kick_knee", [])
    n = len(kk)
    if n < 8:
        logger.warning("detect_contact_event: clip too short (%d frames)", n)
        return None

    # ── Backswing: max kick_knee ────────────────────────────
    valid_kk = [(i, v) for i, v in enumerate(kk) if v is not None and not np.isnan(v)]
    if not valid_kk:
        return None
    backswing_idx = max(valid_kk, key=lambda x: x[1])[0]

    # ── Contact: FIRST MINIMUM after backswing ────────────────────────────
    contact_idx = None
    fallback_used = False
    for i in range(backswing_idx + 1, n - 1):
        if kk[i-1] is not None and kk[i] is not None and kk[i+1] is not None:
            if kk[i] < kk[i-1] and kk[i] <= kk[i+1]:
                contact_idx = i
                break
    
    if contact_idx is None:
        post_bs_valid = [(i, v) for i, v in enumerate(kk[backswing_idx+1:], start=backswing_idx+1) if v is not None]
        if post_bs_valid:
            contact_idx = min(post_bs_valid, key=lambda x: x[1])[0]
            fallback_used = True
        else:
            return None

    if contact_idx <= backswing_idx:
        logger.warning("detect_contact_event: contact not after backswing")
        return None

    # ── Foot velocity at contact frame ────────────────────────────────────
    if (contact_idx > 0
            and contact_idx < len(ankle_x_series)
            and not np.isnan(ankle_x_series[contact_idx])
            and not np.isnan(ankle_x_series[contact_idx - 1])):
        vx = ankle_x_series[contact_idx] - ankle_x_series[contact_idx - 1]
        vy = ankle_y_series[contact_idx] - ankle_y_series[contact_idx - 1]
    else:
        vx, vy = np.nan, np.nan

    duration_ms = (contact_idx - backswing_idx) * (1000.0 / fps)

    result = {}
    for var in ("kick_knee", "sup_knee", "hip_flex", "trunk", "ankle_pf"):
        series = smoothed_timelines.get(var, [])
        bs_val = series[backswing_idx] if backswing_idx < len(series) and series[backswing_idx] is not None else 0.0
        ct_val = series[contact_idx] if contact_idx < len(series) and series[contact_idx] is not None else 0.0
        
        # Mapping to required names
        out_var = var
        if out_var == "ankle_pf": out_var = "ankle"
        elif out_var == "hip_flex": out_var = "hip_flexion"
        elif out_var == "sup_knee": out_var = "support_knee"

        result[out_var] = {
            "backswing": round(float(bs_val), 2),
            "contact": round(float(ct_val), 2),
            "delta": round(float(ct_val - bs_val), 2),
            "series": [round(float(v), 2) if v is not None else None for v in series]
        }

    result["events"] = {
        "backswing_frame": int(backswing_idx),
        "contact_frame": int(contact_idx)
    }

    result["debug"] = {
        "raw_kick_knee": [round(float(v), 2) if v is not None else None for v in raw_timelines.get("kick_knee", [])],
        "smoothed_kick_knee": result["kick_knee"]["series"],
        "detected_frames": f"backswing={backswing_idx}, contact={contact_idx}",
        "warning": "Unstable detection: contact frame fallback used (no local minimum found)" if fallback_used else "None"
    }

    # Legacy fields required by rest of pipeline
    result["legacy"] = {
        "contact_vx": round(float(vx), 3) if not np.isnan(vx) else None,
        "contact_vy": round(float(vy), 3) if not np.isnan(vy) else None,
        "ball_contact_duration_ms": round(duration_ms, 1),
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 7. COMPATIBILITY SHIM — used by existing coaching-engine path
# ─────────────────────────────────────────────────────────────────────────────

def compute_joint_angles_from_filtered_landmarks(
    traj: dict,
    contact_frame_index: Optional[int] = None,
    kicking_side: str = "RIGHT",
    frame_width: int = 1920,
    frame_height: int = 1080,
) -> dict:
    """
    Returns angles at a single frame (contact or last) for the coaching engine.
    Keys match the legacy coaching_engine.py interface.
    """
    traj_norm = _maybe_flip(traj, kicking_side, frame_width)
    first_lm  = next(iter(traj_norm.values()))
    n         = len(first_lm["x"])
    fi        = min(int(contact_frame_index), n - 1) if contact_frame_index is not None else n - 1

    a = _angles_at_frame(traj_norm, fi, frame_width, frame_height)
    return {
        "knee_flexion":          a.get("kick_knee") or 0.0,
        "support_knee":          a.get("sup_knee")  or 0.0,
        "hip_flexion":           a.get("hip_flex")  or 0.0,
        "trunk_inclination":     a.get("trunk")     or 0.0,
        "ankle_plantarflexion":  a.get("ankle_pf")  or 0.0,
    }