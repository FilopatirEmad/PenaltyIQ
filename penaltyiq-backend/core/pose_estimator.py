"""
Pose Estimator — PenaltyIQ Backend
=====================================
Extracts MediaPipe Pose landmarks from video frames.

Design decision [MODEL]:
    MediaPipe Pose is run on the backend (Python) rather than on-device.
    The Flutter frontend uploads the recorded video clip as a byte stream.
    The backend extracts frames, runs MediaPipe, and returns landmark
    trajectories for signal processing.

    Rationale:
        - Avoids 200MB+ on-device model footprint.
        - Backend numpy/scipy stack is already initialised.
        - Consistent landmark extraction across all devices.
        - Enables clinical-grade post-processing (Butterworth filter).

MediaPipe Pose output convention:
    - 33 landmarks per frame.
    - x, y: normalised image coordinates ∈ [0, 1]. [SPEC §1.3.1]
    - z: depth estimate (not used — 2D side-view model). [SPEC §6.1]
    - visibility ∈ [0, 1]: landmark confidence.

Landmark indices used [SPEC §1.5]:
    LEFT_SHOULDER  = 11
    RIGHT_SHOULDER = 12
    LEFT_HIP       = 23
    RIGHT_HIP      = 24
    LEFT_KNEE      = 25
    RIGHT_KNEE     = 26
    LEFT_ANKLE     = 27
    RIGHT_ANKLE    = 28
    LEFT_FOOT_INDEX = 31
    RIGHT_FOOT_INDEX = 32

Scientific basis:
    [WINTER-2009] Ch.3: Joint centre landmarks as proxies for
    rigid body segment endpoints.
    [SPEC §1.3]: Coordinate mapping from normalised → pixel → metric.
"""

import cv2
import numpy as np
import mediapipe as mp
import logging
from dataclasses import dataclass, field
from typing import Optional
from contextlib import suppress
import os
import tempfile

logger = logging.getLogger("penaltyiq.pose_estimator")

# ── MediaPipe landmark name map ───────────────────────────────────────────────
# Maps string names used throughout the pipeline to MediaPipe integer indices.
# Source: MediaPipe Pose Landmark documentation.
LANDMARK_NAME_TO_INDEX: dict[str, int] = {
    "LEFT_SHOULDER":   11,
    "RIGHT_SHOULDER":  12,
    "LEFT_HIP":        23,
    "RIGHT_HIP":       24,
    "LEFT_KNEE":       25,
    "RIGHT_KNEE":      26,
    "LEFT_ANKLE":      27,
    "RIGHT_ANKLE":     28,
    "LEFT_FOOT_INDEX": 31,
    "RIGHT_FOOT_INDEX": 32,
}

# Required landmarks for calibration gate [SPEC §1.6.1]
CALIBRATION_REQUIRED_LANDMARKS: set[str] = {
    "LEFT_SHOULDER",
    "LEFT_HIP",
    "LEFT_KNEE",
    "LEFT_ANKLE",
}

# Required landmarks for kick analysis [SPEC §1.5]
ANALYSIS_REQUIRED_LANDMARKS: set[str] = {
    "LEFT_SHOULDER", "RIGHT_SHOULDER",
    "LEFT_HIP",      "RIGHT_HIP",
    "LEFT_KNEE",     "RIGHT_KNEE",
    "LEFT_ANKLE",    "RIGHT_ANKLE",
    "LEFT_FOOT_INDEX", "RIGHT_FOOT_INDEX",
}


@dataclass
class LandmarkData:
    """
    Normalised landmark coordinates for a single landmark in one frame.

    Coordinate convention [SPEC §1.3.1]:
        x_norm, y_norm ∈ [0, 1].
        Origin: top-left corner of frame.
        x increases rightward, y increases downward.
    """
    x_norm: float
    y_norm: float
    visibility: float


@dataclass
class PoseFrame:
    """
    Complete pose estimation result for a single video frame.
    """
    frame_index: int
    timestamp_ms: float
    landmarks: dict[str, LandmarkData]
    frame_width_px: int
    frame_height_px: int
    pose_detected: bool


@dataclass
class PoseVideoResult:
    """
    Complete pose estimation result for an entire video clip.
    """
    frames: list[PoseFrame]
    total_frames_processed: int
    frames_with_pose: int
    pose_detection_rate: float    # frames_with_pose / total_frames_processed
    fps: float
    frame_width_px: int
    frame_height_px: int
    warnings: list[str] = field(default_factory=list)


class PoseEstimator:
    """
    MediaPipe Pose wrapper for video-based landmark extraction.

    Thread safety: One instance per request (not shared across threads).
    MediaPipe solutions are not thread-safe.
    """

    # MediaPipe model complexity:
    #   0 = lite  (fastest, lowest accuracy)
    #   1 = full  (balanced) ← used for penalty kick analysis
    #   2 = heavy (most accurate, slowest)
    # [MODEL]: complexity=1 chosen as balance between accuracy and
    # server-side throughput. Can be upgraded to 2 for clinical use.
    MODEL_COMPLEXITY: int = 1

    # Minimum detection confidence for pose initialisation.
    # [MODEL]: 0.7 provides reliable detection while rejecting
    # low-confidence frames. [WINTER-2009 Ch.3 recommendation:
    # exclude unreliable landmark data rather than impute.]
    MIN_DETECTION_CONFIDENCE: float = 0.70

    # Minimum tracking confidence for pose tracking between frames.
    MIN_TRACKING_CONFIDENCE: float = 0.70

    def __init__(self):
        self._mp_pose = mp.solutions.pose
        self._pose = self._mp_pose.Pose(
            static_image_mode=False,
            model_complexity=self.MODEL_COMPLEXITY,
            smooth_landmarks=True,
            enable_segmentation=False,
            min_detection_confidence=self.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=self.MIN_TRACKING_CONFIDENCE,
        )
        logger.info(
            f"MediaPipe Pose initialised: "
            f"complexity={self.MODEL_COMPLEXITY}, "
            f"min_detection={self.MIN_DETECTION_CONFIDENCE}"
        )

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        """Release MediaPipe resources."""
        self._pose.close()
        logger.debug("MediaPipe Pose resources released.")

    def process_frame(
        self,
        frame_bgr: np.ndarray,
        frame_index: int,
        timestamp_ms: float
    ) -> PoseFrame:
        """
        Run MediaPipe Pose on a single BGR frame.

        Parameters
        ----------
        frame_bgr : np.ndarray [H, W, 3]
            OpenCV BGR frame.
        frame_index : int
            Zero-based frame number.
        timestamp_ms : float
            Frame timestamp in milliseconds.

        Returns
        -------
        PoseFrame
            Extracted landmarks for this frame.
            pose_detected=False if MediaPipe returns no results.

        Notes
        -----
        MediaPipe expects RGB input. We convert BGR→RGB here.
        [LIMIT][SPEC §6.1]: 2D side-view assumption — z-coordinate
        depth estimates from MediaPipe are discarded.
        """
        h, w = frame_bgr.shape[:2]

        # Convert BGR (OpenCV) → RGB (MediaPipe)
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

        # Make non-writable for performance (avoids copy in MediaPipe)
        frame_rgb.flags.writeable = False
        results = self._pose.process(frame_rgb)
        frame_rgb.flags.writeable = True

        if not results.pose_landmarks:
            return PoseFrame(
                frame_index=frame_index,
                timestamp_ms=timestamp_ms,
                landmarks={},
                frame_width_px=w,
                frame_height_px=h,
                pose_detected=False
            )

        # Extract named landmarks [SPEC §1.3.1]
        landmarks: dict[str, LandmarkData] = {}
        for name, idx in LANDMARK_NAME_TO_INDEX.items():
            lm = results.pose_landmarks.landmark[idx]
            landmarks[name] = LandmarkData(
                x_norm=float(lm.x),
                y_norm=float(lm.y),
                visibility=float(lm.visibility)
            )

        return PoseFrame(
            frame_index=frame_index,
            timestamp_ms=timestamp_ms,
            landmarks=landmarks,
            frame_width_px=w,
            frame_height_px=h,
            pose_detected=True
        )

    def process_video_bytes(
        self,
        video_bytes: bytes,
        max_frames: Optional[int] = None
    ) -> "PoseVideoResult":
        """
        Extract pose landmarks from raw video bytes.

        Writes bytes to a temporary file then delegates to
        process_video_bytes_from_path.  Preserved for backward
        compatibility with existing callers and tests.
        """
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name

        try:
            return self._process_video_from_path(tmp_path, max_frames)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(tmp_path)

    def process_video_bytes_from_path(
        self,
        video_path: str,
        max_frames: Optional[int] = None
    ) -> "PoseVideoResult":
        """
        Extract pose landmarks from a video file that already exists on disk.

        Used by /process-video to avoid a second temp-file write when the
        caller has already saved the upload to a temp file for ball detection.

        Parameters
        ----------
        video_path : str
            Absolute path to an existing video file (MP4, MOV, etc.).
        max_frames : int, optional
            Maximum frames to process.

        Returns
        -------
        PoseVideoResult
        """
        return self._process_video_from_path(video_path, max_frames)

    def _process_video_from_path(
        self,
        tmp_path: str,
        max_frames: Optional[int] = None
    ) -> "PoseVideoResult":
        """
        Internal implementation: open an existing file path with OpenCV
        and run frame-by-frame pose extraction.

        Parameters
        ----------
        tmp_path : str
            Path to an existing video file on disk.
        max_frames : int, optional
            Maximum frames to process. None = process all frames.

        Returns
        -------
        PoseVideoResult

        Notes
        -----
        [SPEC §1.1]: Designed for 60fps smartphone video.
        [LIMIT][SPEC §6.3]: Frame rate is detected from the video
        metadata. If the smartphone encodes at a different rate,
        the fps value is updated accordingly.
        """
        warnings: list[str] = []

        try:
            cap = cv2.VideoCapture(tmp_path)
            if not cap.isOpened():
                raise ValueError(
                    "OpenCV could not open the uploaded video. "
                    "Ensure the file is a valid MP4/MOV format."
                )

            # Extract video metadata
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if fps <= 0:
                fps = 60.0
                warnings.append(
                    "Could not detect video FPS from metadata. "
                    "Defaulting to 60fps. [SPEC §1.1]"
                )

            if abs(fps - 60.0) > 5.0:
                warnings.append(
                    f"Video FPS detected as {fps:.1f} (expected 60fps). "
                    f"Timestamp calculations will use detected FPS. [SPEC §1.1]"
                )

            logger.info(
                f"Processing video: {frame_width}×{frame_height}, "
                f"{fps:.1f}fps, {total_frames} frames."
            )

            # Process frames
            pose_frames: list[PoseFrame] = []
            frame_idx = 0
            frames_with_pose = 0

            while True:
                ret, frame_bgr = cap.read()
                if not ret:
                    break

                if max_frames is not None and frame_idx >= max_frames:
                    break

                timestamp_ms = (frame_idx / fps) * 1000.0

                pose_frame = self.process_frame(
                    frame_bgr, frame_idx, timestamp_ms
                )
                pose_frames.append(pose_frame)

                if pose_frame.pose_detected:
                    frames_with_pose += 1

                frame_idx += 1

            detection_rate = (
                frames_with_pose / frame_idx if frame_idx > 0 else 0.0
            )

            if detection_rate < 0.80:
                warnings.append(
                    f"Pose detection rate: {detection_rate:.1%}. "
                    f"Low detection rate (<80%) may reduce analysis quality. "
                    f"Ensure player is fully visible in the sagittal plane. "
                    f"[SPEC §1.7.2]"
                )

            return PoseVideoResult(
                frames=pose_frames,
                total_frames_processed=frame_idx,
                frames_with_pose=frames_with_pose,
                pose_detection_rate=detection_rate,
                fps=fps,
                frame_width_px=frame_width,
                frame_height_px=frame_height,
                warnings=warnings
            )

        finally:
            cap.release()




def build_calibration_frame_payload(
    pose_result: PoseVideoResult,
    ball_diameters_px: list[float]
) -> list[dict]:
    """
    Convert PoseVideoResult into calibration frame payload
    matching the CalibrationRequest schema.

    Parameters
    ----------
    pose_result : PoseVideoResult
        MediaPipe pose output for the calibration clip.
    ball_diameters_px : list[float]
        Detected ball diameter (pixels) per frame.
        Must have same length as pose_result.frames.
        Use 0.0 for frames where ball is not detected.

    Returns
    -------
    list of dict, matching CalibrationFrame Pydantic schema.
    """
    if len(ball_diameters_px) != len(pose_result.frames):
        raise ValueError(
            f"ball_diameters_px length ({len(ball_diameters_px)}) "
            f"must match pose frames ({len(pose_result.frames)})."
        )

    frames_payload = []

    for i, pose_frame in enumerate(pose_result.frames):
        if not pose_frame.pose_detected:
            continue

        ball_d = ball_diameters_px[i]
        if ball_d <= 0:
            continue    # Skip frames without valid ball detection

        landmarks_dict = {
            name: {
                "x_norm":     lm.x_norm,
                "y_norm":     lm.y_norm,
                "visibility": lm.visibility,
            }
            for name, lm in pose_frame.landmarks.items()
        }

        # Verify required landmarks are present and visible
        missing = CALIBRATION_REQUIRED_LANDMARKS - set(landmarks_dict.keys())
        if missing:
            continue    # Skip frames with missing required landmarks

        frames_payload.append({
            "frame_index":    pose_frame.frame_index,
            "timestamp_ms":   pose_frame.timestamp_ms,
            "landmarks":      landmarks_dict,
            "ball_diameter_px": ball_d,
            "frame_width_px":  pose_frame.frame_width_px,
            "frame_height_px": pose_frame.frame_height_px,
        })

    return frames_payload