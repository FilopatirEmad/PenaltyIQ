"""
Pydantic Schemas — Analysis Endpoint
======================================
Defines request and response contracts for POST /analyze.

This schema is the data contract between the Flutter frontend and the
full analysis pipeline (signal_proc → physics_engine → ik_solver → digital_twin).

Coordinate conventions inherited from calibration_schema.py.
All physics outputs are in SI units (metres, seconds, degrees).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal


# ─── Confidence & Quality Models ─────────────────────────────────────────────

class ConfidenceScore(BaseModel):
    """Composite confidence score for a single analysis result."""
    overall: float = Field(
        ..., ge=0.0, le=1.0,
        description="Weighted composite score ∈ [0, 1]."
    )
    level: Literal["EXCELLENT", "GOOD", "FAIR", "LOW"] = Field(
        ...,
        description="Human-readable confidence band."
    )
    calibration_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Calibration sub-score (weight 40%)."
    )
    pose_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Pose quality sub-score (weight 35%)."
    )
    ball_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Ball detection sub-score (weight 25%)."
    )
    calibration_detail: str = Field(
        ..., description="Plain-English explanation of calibration score."
    )
    pose_detail: str = Field(
        ..., description="Plain-English explanation of pose score."
    )
    ball_detail: str = Field(
        ..., description="Plain-English explanation of ball score."
    )
    summary: str = Field(
        ..., description="Single-sentence overall confidence summary for the UI."
    )


class InputQualityReport(BaseModel):
    """Pre-analysis quality assessment emitted alongside analysis results."""
    usable: bool = Field(
        ...,
        description="False = video is too poor for reliable analysis."
    )
    quality_level: Literal["GOOD", "FAIR", "POOR", "UNUSABLE"] = Field(
        ...,
        description="Overall video/input quality classification."
    )
    issues: list[str] = Field(
        default_factory=list,
        description="Machine-readable issue codes (e.g. 'low_pose_detection')."
    )
    user_messages: list[str] = Field(
        default_factory=list,
        description="Plain-English descriptions of each issue, shown in the app."
    )
    suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable improvement hints for the user."
    )


class PlayerScore(BaseModel):
    """Overall player performance score out of 100."""
    score: int = Field(
        ..., 
        ge=0, le=100, 
        description="Overall technique score [0, 100]."
    )
    level: Literal["Beginner", "Good", "Pro"] = Field(
        ..., 
        description="Classification based on score."
    )
    breakdown: dict[str, int] = Field(
        ..., 
        description="Sub-scores for each coached variable [0, 100]."
    )


class AnalysisSummary(BaseModel):
    """Aggregated summary for the frontend's final 'Summary Screen'."""
    player_score: int = Field(..., description="Overall technique score [0, 100].")
    player_level: str = Field(..., description="Beginner, Good, or Pro.")
    top_insight: str = Field(..., description="The most critical piece of coaching feedback.")
    ball_speed_kmh: float = Field(..., description="Measured ball speed in km/h.")
    target_hit: bool = Field(..., description="Did the ball hit the intended goal zone?")
    zone_hit: str = Field(..., description="The actual zone the ball hit.")


# ─── Sub-Models: Request ─────────────────────────────────────────────────────

class NormalisedLandmark(BaseModel):
    x_norm: float = Field(..., description="Normalised x [-inf, inf] off-screen allowed")
    y_norm: float = Field(..., description="Normalised y [-inf, inf] off-screen allowed")
    visibility: float = Field(..., ge=0.0, le=1.0)


class BallCenter(BaseModel):
    """Ball centre in pixel coordinates for a single frame."""
    x_px: float = Field(..., ge=0.0, description="Ball centre x in pixels.")
    y_px: float = Field(..., ge=0.0, description="Ball centre y in pixels.")


class AnalysisFrame(BaseModel):
    """
    A single frame from the kick video.
    Provides both pose landmarks and ball tracking data.
    """
    frame_index: int = Field(..., ge=0)
    timestamp_ms: float = Field(..., ge=0.0)
    landmarks: dict[str, NormalisedLandmark] = Field(
        ...,
        description="MediaPipe Pose landmarks for this frame."
    )
    ball_center_px: Optional[BallCenter] = Field(
        None,
        description=(
            "Ball centre in pixel coordinates. Required for frames "
            "immediately after foot contact (for v0 estimation). "
            "None for frames where ball is not detected."
        )
    )
    frame_width_px: int = Field(..., gt=0)
    frame_height_px: int = Field(..., gt=0)


class LockedCalibration(BaseModel):
    """
    Player-specific calibration constants locked by the calibration gate.
    Must be forwarded from the CalibrationResponse to every analysis request.

    If gate_passed_with_fallback is True, segments come from population
    averages [WINTER-2009] rather than player-specific measurement.
    The confidence engine uses this to reduce the calibration sub-score.
    """
    scale_m_per_px: float = Field(
        ..., gt=0.0,
        description="S = 0.22 / d_ball_px [m/pixel]. From calibration gate."
    )
    thigh_m: float = Field(..., gt=0.0, description="Locked thigh length [m].")
    shank_m: float = Field(..., gt=0.0, description="Locked shank length [m].")
    trunk_m: float = Field(..., gt=0.0, description="Locked trunk length [m].")
    leg_m: float   = Field(..., gt=0.0, description="thigh_m + shank_m [m].")

    # Calibration quality metadata — forwarded from /process-video response
    gate_passed: bool = Field(
        default=True,
        description="True if strict calibration gate passed."
    )
    gate_passed_with_fallback: bool = Field(
        default=False,
        description="True if a relaxed or anthropometric fallback was used."
    )
    fallback_reason: Optional[str] = Field(
        default=None,
        description="Identifies which fallback tier was applied."
    )
    thigh_variation_m: float = Field(
        default=0.0,
        description="Thigh variation over calibration window [m]."
    )
    thigh_tolerance_m: float = Field(
        default=0.01,
        description="Allowed thigh variation threshold [m]."
    )
    frames_used: int = Field(
        default=120,
        description="Number of calibration frames used."
    )


class AnalysisRequest(BaseModel):
    """
    Full request payload for POST /analyze.
    """
    session_id: str = Field(..., description="UUID v4. Must match calibration session.")
    goal_zone: Literal["T1","T2","T3","T4","B1","B2","B3","B4"] = Field(
        ...,
        description=(
            "Target goal zone selected by the user in the Flutter UI. "
            "Defines (x_target, y_target) for the physics engine. [SPEC §2.3]"
        )
    )
    calibration: LockedCalibration = Field(
        ...,
        description="Locked calibration constants from POST /calibrate response."
    )
    frames: list[AnalysisFrame] = Field(
        ...,
        min_length=10,
        description=(
            "Ordered frames from the kick video. Must include: "
            "(a) approach frames for pose analysis, "
            "(b) contact frame and ≥ 3 post-contact frames for v0 estimation."
        )
    )
    fps: float = Field(
        default=60.0,
        gt=0.0,
        description="Video frame rate. Default 60fps. [SPEC §1.1]"
    )
    contact_frame_index: Optional[int] = Field(
        default=None,
        ge=0,
        description=(
            "Optional contact frame index from /process-video. "
            "When provided, post-contact ball frames are selected from this index."
        )
    )


# ─── Sub-Models: Response ────────────────────────────────────────────────────

class PhysicsResult(BaseModel):
    """Output of the inverse projectile engine."""
    v0_measured_ms: float = Field(
        ...,
        description="Estimated ball launch speed [m/s]. [SPEC §2.4]"
    )
    theta_v_deg: float = Field(
        ...,
        description="Required vertical launch angle [degrees]. [SPEC §2.5.2]"
    )
    theta_h_deg: float = Field(
        ...,
        description="Required horizontal deflection angle [degrees]. [SPEC §2.5.1]"
    )
    speed_regime: Literal["HIGH", "MODERATE", "LOW"] = Field(
        ...,
        description=(
            "Speed regime classification. [SPEC §2.7] "
            "HIGH: v0 ≥ 20 m/s, MODERATE: 14–20 m/s, LOW: < 14 m/s."
        )
    )
    feasibility: Literal["HIGH", "MODERATE", "LOW"] = Field(
        ...,
        description=(
            "Zone feasibility at this v0. LOW means extreme loft required. [SPEC §2.7.1]"
        )
    )
    crossbar_clearance_m: float = Field(
        ...,
        description=(
            "Predicted vertical clearance below crossbar at x=D [m]. "
            "Must be ≥ CROSSBAR_SAFETY_MARGIN_M = 0.15m. [SPEC §2.8]"
        )
    )
    safety_margin_satisfied: bool = Field(
        ...,
        description="True if crossbar clearance ≥ 0.15m. [SPEC §2.8]"
    )


class IKResult(BaseModel):
    """Output of the constrained IK solver."""
    hip_flexion_deg: float
    knee_angle_deg: float
    ankle_plantarflexion_deg: float = Field(0.0, description="Deprecated, 0.0")
    support_leg_knee_deg: float
    trunk_inclination_deg: float
    solver_converged: bool
    residual: float = Field(
        ...,
        description="Final cost function value J(q*). < 0.01 = good convergence."
    )


class DigitalTwinResult(BaseModel):
    """Output of the forward verification simulation."""
    predicted_x_m: float
    predicted_y_m: float
    zone_hit: str
    verification_passed: bool
    x_error_m: float = Field(
        ...,
        description="Horizontal error: |predicted_x - target_x| [m]."
    )
    y_error_m: float = Field(
        ...,
        description="Vertical error: |predicted_y - target_y| [m]."
    )


class CoachingFeedbackItem(BaseModel):
    """A single coaching feedback item for one kinematic variable."""
    variable: str
    measured_deg: float
    target_deg: float
    target_range_min_deg: float
    target_range_max_deg: float
    delta_deg: float = Field(
        ...,
        description=(
            "Signed deviation: measured - target. "
            "Positive = exceeds target, Negative = below target."
        )
    )
    status: Literal["OPTIMAL", "ACCEPTABLE", "NEEDS_WORK", "CRITICAL"]
    cue: str = Field(..., description="Plain-English coaching instruction.")


class BiomechVariable(BaseModel):
    backswing: float
    contact: float
    delta: float
    series: list[Optional[float]]

class BiomechEvents(BaseModel):
    backswing_frame: int
    contact_frame: int

class LegacyKinematics(BaseModel):
    contact_vx: Optional[float]
    contact_vy: Optional[float]
    ball_contact_duration_ms: float

class StrictBiomechanicsResult(BaseModel):
    """Output of the strict biomechanics pipeline matching Sports2D."""
    kick_knee: BiomechVariable
    support_knee: BiomechVariable
    hip_flexion: BiomechVariable
    trunk: BiomechVariable
    ankle: BiomechVariable
    events: BiomechEvents
    debug: dict
    legacy: LegacyKinematics


class AnalysisResponse(BaseModel):
    """Complete response payload for POST /analyze."""
    session_id: str
    goal_zone: str
    physics: PhysicsResult
    contact_frame_index: Optional[int] = Field(
        default=None, 
        description="The index of the frame where ball contact occurred."
    )
    ik_result: Optional[IKResult] = None
    strict_biomechanics: Optional[StrictBiomechanicsResult] = None
    digital_twin: Optional[DigitalTwinResult] = None
    coaching_feedback: list[CoachingFeedbackItem] = Field(default_factory=list)
    pipeline_warnings: list[str] = Field(
        default_factory=list,
        description="Non-fatal warnings (e.g., low v0 → LOW feasibility)."
    )
    confidence: Optional[ConfidenceScore] = Field(
        default=None,
        description=(
            "Composite confidence score ∈ [0, 1]. "
            "Built from calibration quality, pose quality, and ball detection reliability. "
            "Displayed in the UI to set user expectations."
        )
    )
    input_quality: Optional[InputQualityReport] = Field(
        default=None,
        description=(
            "Input quality assessment. "
            "Flags issues (low pose rate, missing ball, etc.) "
            "with plain-English messages and actionable suggestions."
        )
    )
    player_score: Optional[PlayerScore] = Field(
        default=None,
        description="0-100 technique score based on deviation from IK targets."
    )
    angle_timelines: Optional[dict[str, list[Optional[float]]]] = Field(
        default=None,
        description="Frame-by-frame joint angles for frontend graphing."
    )
    compressed_keypoints: Optional[dict[str, list[list[float]]]] = Field(
        default=None,
        description="Frame-by-frame metric keypoints [x_m, y_m] for frontend skeleton overlay."
    )
    summary: Optional[AnalysisSummary] = Field(
        default=None,
        description="Aggregated data specifically structured for the final UI summary screen."
    )