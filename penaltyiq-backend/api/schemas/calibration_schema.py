"""
Pydantic Schemas — Calibration Endpoint
========================================
Defines the complete request and response contracts for POST /calibrate.

Design principle: Every field has an explicit description and unit annotation.
No implicit assumptions about coordinate systems or units.

Coordinate convention (documented here, enforced everywhere):
  - x_norm, y_norm: MediaPipe normalised image coordinates ∈ [0, 1]
    Origin: top-left corner of frame.
    x increases rightward, y increases downward.
    Source: MediaPipe Pose documentation.
  - x_px, y_px: Pixel coordinates after un-normalisation.
    x_px = x_norm × frame_width_px
    y_px = y_norm × frame_height_px
  - x_m, y_m: Metric coordinates after scale factor application.
    x_m = x_px × S,  where S = 0.22 / d_ball_px  [m/pixel]
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional


# ─── Sub-Models ──────────────────────────────────────────────────────────────

class NormalisedLandmark(BaseModel):
    """
    A single MediaPipe Pose landmark in normalised image coordinates.
    MediaPipe returns x, y ∈ [0, 1] normalised to frame dimensions.
    visibility ∈ [0, 1]: landmark detection confidence.
    """
    x_norm: float = Field(
        ...,
        description="Normalised x coordinate, origin at left edge of frame. Can be slightly outside [0,1]."
    )
    y_norm: float = Field(
        ...,
        description="Normalised y coordinate, origin at top edge of frame. Can be slightly outside [0,1]."
    )
    visibility: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="MediaPipe landmark visibility/confidence score ∈ [0,1]."
    )


class CalibrationFrame(BaseModel):
    """
    A single frame of T-pose calibration data.

    Required landmarks for segment length computation:
      - LEFT_SHOULDER  → LEFT_HIP: trunk length
      - LEFT_HIP       → LEFT_KNEE: thigh length
      - LEFT_KNEE      → LEFT_ANKLE: shank length

    [WINTER-2009] Ch.3: Segment length computed as Euclidean distance
    between proximal and distal joint centre landmarks.
    """
    frame_index: int = Field(
        ...,
        ge=0,
        description="Zero-based frame index within the calibration clip."
    )
    timestamp_ms: float = Field(
        ...,
        ge=0.0,
        description="Frame timestamp in milliseconds from start of clip."
    )
    landmarks: dict[str, NormalisedLandmark] = Field(
        ...,
        description=(
            "Dictionary of MediaPipe landmark name → normalised coordinate. "
            "Required keys: LEFT_SHOULDER, LEFT_HIP, LEFT_KNEE, LEFT_ANKLE. "
            "RIGHT-side landmarks included if available for bilateral check."
        )
    )
    ball_diameter_px: float = Field(
        ...,
        gt=0.0,
        description=(
            "Detected ball diameter in pixels for this frame. "
            "Used to compute S = 0.22 / ball_diameter_px [m/pixel]. "
            "[FIFA-2024]: ball diameter = 0.22 m."
        )
    )
    frame_width_px: int = Field(
        ...,
        gt=0,
        description="Full frame width in pixels (e.g., 1920 for 1080p)."
    )
    frame_height_px: int = Field(
        ...,
        gt=0,
        description="Full frame height in pixels (e.g., 1080 for 1080p)."
    )

    @field_validator("landmarks")
    @classmethod
    def validate_required_landmarks(
        cls, v: dict[str, NormalisedLandmark]
    ) -> dict[str, NormalisedLandmark]:
        """
        Enforce presence of the four landmarks required for segment
        length computation. Fails fast with explicit error message
        before any computation occurs.
        """
        REQUIRED: set[str] = {
            "LEFT_SHOULDER",
            "LEFT_HIP",
            "LEFT_KNEE",
            "LEFT_ANKLE",
        }
        missing = REQUIRED - set(v.keys())
        if missing:
            raise ValueError(
                f"CalibrationFrame is missing required landmarks: {missing}. "
                f"All four landmarks {REQUIRED} must be present and detected "
                f"with visibility > 0."
            )
        return v


class CalibrationRequest(BaseModel):
    """
    Full request payload for POST /calibrate.

    The frontend sends all frames from the T-pose calibration clip.
    Minimum: 2 seconds × 60 fps = 120 frames.
    The backend applies the stability gate over the full sequence.
    """
    session_id: str = Field(
        ...,
        description="UUID v4 session identifier. Ties calibration to analysis."
    )
    frames: list[CalibrationFrame] = Field(
        ...,
        min_length=15,   # absolute minimum for filter stability
        description=(
            "Ordered list of calibration frames (T-pose). "
            "Clinical minimum: 120 frames (2s × 60fps). "
            "The stability gate requires ≥ 2s of data. [SPEC §1.6.1]"
        )
    )

    @field_validator("frames")
    @classmethod
    def validate_frame_ordering(
        cls, v: list[CalibrationFrame]
    ) -> list[CalibrationFrame]:
        """Enforce monotonically increasing frame indices."""
        indices = [f.frame_index for f in v]
        if indices != sorted(indices):
            raise ValueError(
                "Calibration frames must be ordered by frame_index "
                "(ascending). Received out-of-order sequence."
            )
        return v


# ─── Response Models ──────────────────────────────────────────────────────────

class StabilityCheckResult(BaseModel):
    """
    Result of the bounded-variation stability criterion.
    [SPEC §1.6.1]: max(Lk) - min(Lk) ≤ εk over T=2s window.
    """
    thigh_variation_m: float = Field(
        ...,
        description="max(L_thigh) - min(L_thigh) over the stability window [m]."
    )
    shank_variation_m: float = Field(
        ...,
        description="max(L_shank) - min(L_shank) over the stability window [m]."
    )
    trunk_variation_m: float = Field(
        ...,
        description="max(L_trunk) - min(L_trunk) over the stability window [m]."
    )
    thigh_tolerance_m: float = Field(
        ...,
        description="Tolerance εk for thigh = 0.02 × L_thigh_median [m]. [SPEC §1.6.1]"
    )
    shank_tolerance_m: float = Field(
        ...,
        description="Tolerance εk for shank = 0.02 × L_shank_median [m]. [SPEC §1.6.1]"
    )
    trunk_tolerance_m: float = Field(
        ...,
        description="Tolerance εk for trunk = 0.02 × L_trunk_median [m]. [SPEC §1.6.1]"
    )
    window_duration_s: float = Field(
        ...,
        description="Duration of the stability evaluation window in seconds."
    )
    thigh_passed: bool
    shank_passed: bool
    trunk_passed: bool
    overall_passed: bool = Field(
        ...,
        description=(
            "True only if ALL three segments pass the stability criterion. "
            "Hard gate: analysis is blocked if False. [SPEC §1.6.1]"
        )
    )


class LockedSegments(BaseModel):
    """
    Player-specific segment lengths locked by the calibration gate.
    Computed as median over the stable window. [WINTER-2009 Ch.3]
    These constants are forwarded to the IK solver for all subsequent
    analysis of this session.
    """
    thigh_m: float = Field(
        ...,
        gt=0.0,
        description="Kicking-leg thigh length: hip centre → knee centre [m]. [WINTER-2009]"
    )
    shank_m: float = Field(
        ...,
        gt=0.0,
        description="Kicking-leg shank length: knee centre → ankle centre [m]. [WINTER-2009]"
    )
    trunk_m: float = Field(
        ...,
        gt=0.0,
        description="Trunk length: hip centre → shoulder centre [m]. [WINTER-2009]"
    )
    leg_m: float = Field(
        ...,
        gt=0.0,
        description=(
            "Total leg length: L_thigh + L_shank [m]. "
            "Derived segment — not independently measured. [SPEC §1.3.4]"
        )
    )


class CalibrationResponse(BaseModel):
    """
    Response payload for POST /calibrate.
    status='LOCKED' indicates the hard gate passed and analysis may proceed.
    status='FAILED' indicates the stability criterion was not met.
    """
    session_id: str
    status: str = Field(
        ...,
        pattern="^(LOCKED|FAILED|INSUFFICIENT_DATA)$",
        description=(
            "LOCKED: gate passed, segments stored, analysis permitted. "
            "FAILED: stability criterion not met, player must re-calibrate. "
            "INSUFFICIENT_DATA: fewer than 120 frames provided."
        )
    )
    scale_m_per_px: Optional[float] = Field(
        None,
        description=(
            "Pixel-to-metre scale factor S = 0.22 / d_ball_px [m/pixel]. "
            "Computed as median over all calibration frames. [FIFA-2024, SPEC §1.2.1]"
        )
    )
    segments_m: Optional[LockedSegments] = Field(
        None,
        description="Locked segment lengths. None if status != LOCKED."
    )
    stability_check: StabilityCheckResult = Field(
        ...,
        description="Detailed stability gate results for each segment."
    )
    frames_used: int = Field(
        ...,
        description="Number of frames included in the stability window."
    )
    error: Optional[str] = Field(
        None,
        description="Human-readable error message if status != LOCKED."
    )