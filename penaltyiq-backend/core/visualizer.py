"""
Visualizer — PenaltyIQ Backend
==============================
Generates an overlaid video showing the pose skeleton, key angles,
and ball trajectory for visual feedback to the user.
"""

import cv2
import tempfile
import os
import math
import numpy as np
from typing import Optional, Dict, List, Any

# MediaPipe pose connections for the skeleton
POSE_CONNECTIONS = [
    ("LEFT_SHOULDER", "RIGHT_SHOULDER"),
    ("LEFT_SHOULDER", "LEFT_ELBOW"),
    ("LEFT_ELBOW", "LEFT_WRIST"),
    ("RIGHT_SHOULDER", "RIGHT_ELBOW"),
    ("RIGHT_ELBOW", "RIGHT_WRIST"),
    ("LEFT_SHOULDER", "LEFT_HIP"),
    ("RIGHT_SHOULDER", "RIGHT_HIP"),
    ("LEFT_HIP", "RIGHT_HIP"),
    ("LEFT_HIP", "LEFT_KNEE"),
    ("LEFT_KNEE", "LEFT_ANKLE"),
    ("RIGHT_HIP", "RIGHT_KNEE"),
    ("RIGHT_KNEE", "RIGHT_ANKLE"),
    ("LEFT_ANKLE", "LEFT_FOOT_INDEX"),
    ("RIGHT_ANKLE", "RIGHT_FOOT_INDEX"),
]

def rotate_point(origin, point, angle_deg):
    """Rotate a point counterclockwise by a given angle around a given origin."""
    ox, oy = origin
    px, py = point
    angle_rad = math.radians(angle_deg)
    qx = ox + math.cos(angle_rad) * (px - ox) - math.sin(angle_rad) * (py - oy)
    qy = oy + math.sin(angle_rad) * (px - ox) + math.cos(angle_rad) * (py - oy)
    return int(qx), int(qy)

def render_overlay_video(
    video_path: str,
    analysis_data: Dict[str, Any],
    scale_m_per_px: float,
) -> str:
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if fps == 0 or math.isnan(fps):
        fps = 30.0
        
    out_fd, out_path = tempfile.mkstemp(suffix=".mp4")
    os.close(out_fd)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (width, height))
    
    compressed_keypoints = analysis_data.get("compressed_keypoints", {})
    angle_timelines = analysis_data.get("angle_timelines", {})
    player_score = analysis_data.get("player_score", {})
    contact_frame = analysis_data.get("contact_frame_index")
    coaching = analysis_data.get("coaching_feedback", [])
    physics = analysis_data.get("physics", {})
    
    # Kicking leg definition
    KICK_HIP = "LEFT_HIP"
    KICK_KNEE = "LEFT_KNEE"
    KICK_ANKLE = "LEFT_ANKLE"
    KICK_FOOT = "LEFT_FOOT_INDEX"
    KICK_SHOULDER = "LEFT_SHOULDER"
    
    # Extract total frames
    n_frames = 0
    if compressed_keypoints:
        first_key = next(iter(compressed_keypoints))
        n_frames = len(compressed_keypoints[first_key])
        
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        if frame_idx < n_frames:
            # 1. Overlay Pose Skeleton
            points_px = {}
            for lm_name, coords in compressed_keypoints.items():
                if frame_idx < len(coords):
                    x_m, y_m = coords[frame_idx]
                    x_px = int(x_m / scale_m_per_px)
                    y_px = int(y_m / scale_m_per_px)
                    points_px[lm_name] = (x_px, y_px)
                    cv2.circle(frame, (x_px, y_px), 4, (0, 255, 255), -1)
            
            # Draw standard connections
            for p1, p2 in POSE_CONNECTIONS:
                if p1 in points_px and p2 in points_px:
                    # Highlight kicking leg
                    is_kicking_leg = (p1 in [KICK_HIP, KICK_KNEE, KICK_ANKLE, KICK_FOOT] and 
                                      p2 in [KICK_HIP, KICK_KNEE, KICK_ANKLE, KICK_FOOT])
                    color = (0, 165, 255) if is_kicking_leg else (255, 0, 0) # Orange for kicking leg, blue for rest
                    thickness = 4 if is_kicking_leg else 2
                    cv2.line(frame, points_px[p1], points_px[p2], color, thickness)
            
            # Highlight Key Angles
            if "knee_flexion" in angle_timelines and frame_idx < len(angle_timelines["knee_flexion"]):
                knee_angle = angle_timelines["knee_flexion"][frame_idx]
                if knee_angle is not None and KICK_KNEE in points_px:
                    kx, ky = points_px[KICK_KNEE]
                    cv2.putText(
                        frame, f"{knee_angle:.1f} deg", (kx + 15, ky),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
                    )

            # Contact Frame Special Effects
            if contact_frame is not None and abs(frame_idx - contact_frame) <= 5:
                # Ghost Skeleton Overlay (Ideal Form) at Contact
                if frame_idx == contact_frame:
                    cv2.putText(frame, "CONTACT FRAME", (width // 2 - 100, height // 2 - 200),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 3)
                                
                    if KICK_HIP in points_px and KICK_KNEE in points_px and KICK_ANKLE in points_px:
                        # Find deltas from coaching feedback
                        knee_delta = next((item["delta_deg"] for item in coaching if item["variable"] == "knee_flexion"), 0)
                        trunk_delta = next((item["delta_deg"] for item in coaching if item["variable"] == "trunk_inclination"), 0)
                        
                        # Calculate ideal points
                        hip = points_px[KICK_HIP]
                        actual_knee = points_px[KICK_KNEE]
                        actual_ankle = points_px[KICK_ANKLE]
                        
                        # Rotate to find ghost points (visual approximation)
                        ideal_knee = rotate_point(hip, actual_knee, -knee_delta * 0.5)
                        ideal_ankle = rotate_point(ideal_knee, (actual_ankle[0] + ideal_knee[0] - actual_knee[0], actual_ankle[1] + ideal_knee[1] - actual_knee[1]), -knee_delta * 0.5)
                        
                        # Draw Ghost Leg
                        overlay = frame.copy()
                        cv2.line(overlay, hip, ideal_knee, (255, 255, 255), 4, cv2.LINE_AA)
                        cv2.line(overlay, ideal_knee, ideal_ankle, (255, 255, 255), 4, cv2.LINE_AA)
                        cv2.circle(overlay, ideal_knee, 6, (255, 255, 255), -1)
                        cv2.circle(overlay, ideal_ankle, 6, (255, 255, 255), -1)
                        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
                        
                        cv2.putText(frame, "Ideal Form", (ideal_knee[0] + 20, ideal_knee[1] - 20),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                        
                # Draw Ball Trajectory Arrow
                if physics and frame_idx >= contact_frame and KICK_FOOT in points_px:
                    theta_v = physics.get("theta_v_deg", 15.0)
                    theta_h = physics.get("theta_h_deg", 0.0)
                    v0 = physics.get("v0_measured_ms", 20.0)
                    
                    start_px = points_px[KICK_FOOT]
                    # Simulate trajectory end point in 2D
                    end_px = (
                        int(start_px[0] + v0 * 5 * math.sin(math.radians(theta_h))),
                        int(start_px[1] - v0 * 5 * math.cos(math.radians(theta_v)))
                    )
                    cv2.arrowedLine(frame, start_px, end_px, (0, 0, 255), 4, tipLength=0.2)
                        
        # 3. Draw overall score
        if player_score:
            score = player_score.get("score", 0)
            level = player_score.get("level", "")
            cv2.putText(
                frame, f"PenaltyIQ Score: {score}/100", (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 255), 3
            )
            cv2.putText(
                frame, f"Level: {level}", (20, 90),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 200, 255), 2
            )
            
        out.write(frame)
        
        # SLOW MOTION: write frame multiple times near contact
        if contact_frame is not None and abs(frame_idx - contact_frame) <= 5:
            out.write(frame)
            out.write(frame)
            out.write(frame)
            
        frame_idx += 1
        
    cap.release()
    out.release()
    return out_path
