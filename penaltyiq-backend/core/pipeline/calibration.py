import math
import statistics
from typing import List, Dict, Any

class LockedSegments:
    def __init__(self, thigh_m: float, shank_m: float, trunk_m: float, leg_m: float):
        self.thigh_m = thigh_m
        self.shank_m = shank_m
        self.trunk_m = trunk_m
        self.leg_m = leg_m

class LockedCalibration:
    def __init__(self, scale_m_per_px: float, segments_m: LockedSegments, confidence_score: float, pipeline_warnings: List[str]):
        self.scale_m_per_px = scale_m_per_px
        self.segments_m = segments_m
        self.confidence_score = confidence_score
        self.pipeline_warnings = pipeline_warnings
        # Forward compatibility shim if old physics core still expects the boolean locally
        self.stability_check = confidence_score > 0.5 

def filter_outliers_iqr(data: List[float]) -> List[float]:
    if len(data) < 4:
        return data
    sorted_data = sorted(data)
    q1 = sorted_data[len(sorted_data) // 4]
    q3 = sorted_data[(3 * len(sorted_data)) // 4]
    iqr = q3 - q1
    return [d for d in data if (q1 - 1.5 * iqr) <= d <= (q3 + 1.5 * iqr)]

def run_auto_calibration(frames: List[Dict[str, Any]], video_width: int, video_height: int) -> LockedCalibration:
    warnings = []
    FIFA_BALL_DIAMETER_M = 0.22
    
    # 1. BALL DIAMETER CALCULATION
    raw_diameters = [f["ball_diameter_px"] for f in frames if f.get("ball_diameter_px")]
    if not raw_diameters:
        raise ValueError("Calibration failed: Ball never detected in video.")
        
    filtered_diameters = filter_outliers_iqr(raw_diameters)
    median_diameter_px = statistics.median(filtered_diameters if filtered_diameters else raw_diameters)
    
    if median_diameter_px <= 0:
        raise ValueError("Calibration failed: Computed ball diameter is <= 0.")
        
    scale_m_per_px = FIFA_BALL_DIAMETER_M / median_diameter_px

    # 2. STABLE MULTI-FRAME & BILATERAL SELECTION WITH VISIBILITY THRESHOLDS
    def calc_distance(p1: dict, p2: dict) -> float:
        x1, y1 = p1['x_norm'] * video_width, p1['y_norm'] * video_height
        x2, y2 = p2['x_norm'] * video_width, p2['y_norm'] * video_height
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    valid_frames = []
    used_fallback_side = False
    visibility_threshold = 0.6

    for f in frames:
        lms = f.get("landmarks", {})
        side = None
        
        # Check LEFT side first
        if all(k in lms for k in ["LEFT_HIP", "LEFT_KNEE", "LEFT_ANKLE", "LEFT_SHOULDER"]):
            if all(lms[f"LEFT_{j}"].get("visibility", 0) >= visibility_threshold for j in ["HIP", "KNEE", "ANKLE", "SHOULDER"]):
                side = "LEFT"
                
        # Fallback to RIGHT side if LEFT fails
        if not side and all(k in lms for k in ["RIGHT_HIP", "RIGHT_KNEE", "RIGHT_ANKLE", "RIGHT_SHOULDER"]):
            if all(lms.get(f"RIGHT_{j}", {}).get("visibility", 0) >= visibility_threshold for j in ["HIP", "KNEE", "ANKLE", "SHOULDER"]):
                side = "RIGHT"
                used_fallback_side = True
                
        if side:
            try:
                vis = sum(lms[f"{side}_{j}"].get("visibility", 0) for j in ["HIP", "KNEE", "ANKLE", "SHOULDER"])
                valid_frames.append({"frame": f, "side": side, "vis": vis})
            except KeyError:
                continue

    # 3. MINIMUM FRAME COUNT VALIDATION
    if len(valid_frames) < 5:
        raise ValueError(f"Calibration failed: insufficient valid frames ({len(valid_frames)}) for stable estimation. Minimum required is 5.")

    if used_fallback_side:
        warnings.append("Using fallback (RIGHT) side for calibration due to poor LEFT side visibility.")

    valid_frames.sort(key=lambda x: x["vis"], reverse=True)
    top_frames = valid_frames[:3]

    thighs, shanks, trunks = [], [], []
    for tf in top_frames:
        lms = tf["frame"]["landmarks"]
        side = tf["side"]
        thighs.append(calc_distance(lms[f"{side}_HIP"], lms[f"{side}_KNEE"]))
        shanks.append(calc_distance(lms[f"{side}_KNEE"], lms[f"{side}_ANKLE"]))
        trunks.append(calc_distance(lms[f"{side}_SHOULDER"], lms[f"{side}_HIP"]))

    segments = LockedSegments(
        thigh_m=statistics.mean(thighs) * scale_m_per_px,
        shank_m=statistics.mean(shanks) * scale_m_per_px,
        trunk_m=statistics.mean(trunks) * scale_m_per_px,
        leg_m=(statistics.mean(thighs) + statistics.mean(shanks)) * scale_m_per_px
    )

    # 4. CONFIDENCE SCORING & BIOMECHANICAL VALIDATION
    avg_visibility = statistics.mean([tf["vis"] / 4.0 for tf in top_frames]) if top_frames else 0
    frame_score = min(1.0, len(valid_frames) / 10.0)
    base_confidence = 0.6 * frame_score + 0.4 * avg_visibility
    
    if segments.shank_m < 1e-6:
        ratio = 0
    else:
        ratio = segments.thigh_m / segments.shank_m
    
    if not (0.8 < ratio < 1.5):
        base_confidence *= 0.5  # Penalize severe anatomical anomalies
        warnings.append("Unstable pose detection: Anatomical proportions appear incorrect.")

    if base_confidence < 0.5:
        warnings.append("Low overall calibration confidence.")

    return LockedCalibration(
        scale_m_per_px=scale_m_per_px, 
        segments_m=segments, 
        confidence_score=round(base_confidence, 2),
        pipeline_warnings=warnings
    )
