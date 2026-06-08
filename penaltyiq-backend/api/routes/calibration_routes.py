"""
Calibration Route — POST /api/v1/calibrate
============================================
FastAPI route handler. Validates input, calls the calibration pipeline,
and returns a structured response.

Standard response wrapper applied:
  {"success": true, "data": <CalibrationResponse>, "message": ""}
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
import logging

from api.schemas.calibration_schema import (
    CalibrationRequest,
    CalibrationResponse,
    StabilityCheckResult,
    LockedSegments,
)
from api.schemas.response import ok
from api.dependencies import get_current_user
from core.calibration import run_calibration_pipeline, CalibrationResult
from core.rate_limiter import limiter
from config import settings

router = APIRouter()
logger = logging.getLogger("penaltyiq.routes.calibration")


@router.post(
    "/calibrate",
    status_code=status.HTTP_200_OK,
    summary="Static Calibration Gate",
    description=(
        "Receives T-pose frames, computes pixel-to-metre scale from ball diameter, "
        "applies 2-second stability gate on segment lengths, and locks "
        "player-specific thigh/shank/trunk constants. [SPEC §1.6.1]"
    ),
)
@limiter.limit(settings.rate_limit_calibrate)
async def calibrate(
    request: Request,
    body: CalibrationRequest,
    _user=Depends(get_current_user),
):
    """
    POST /calibrate

    Hard Gate Behaviour:
        - Returns status='LOCKED' only if all stability criteria are met.
        - Returns status='FAILED' or 'INSUFFICIENT_DATA' otherwise.
        - The frontend MUST NOT proceed to recording if status != 'LOCKED'.
    """
    logger.info(
        f"Calibration request received. "
        f"Session: {body.session_id}. "
        f"Frames: {len(body.frames)}."
    )

    try:
        request_dict = {
            "session_id": body.session_id,
            "frames": [
                {
                    "frame_index": f.frame_index,
                    "timestamp_ms": f.timestamp_ms,
                    "landmarks": {
                        name: {
                            "x_norm": lm.x_norm,
                            "y_norm": lm.y_norm,
                            "visibility": lm.visibility,
                        }
                        for name, lm in f.landmarks.items()
                    },
                    "ball_diameter_px": f.ball_diameter_px,
                    "frame_width_px": f.frame_width_px,
                    "frame_height_px": f.frame_height_px,
                }
                for f in body.frames
            ],
        }

        result: CalibrationResult = run_calibration_pipeline(request_dict)

    except ValueError as e:
        logger.error(f"Calibration pipeline ValueError: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Calibration input error: {str(e)}",
        )
    except Exception as e:
        logger.exception(f"Unexpected calibration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal calibration error. Check server logs.",
        )

    # ── Build response ──────────────────────────────────────────────────────
    stability_result = StabilityCheckResult(
        thigh_variation_m=result.thigh_variation_m,
        shank_variation_m=result.shank_variation_m,
        trunk_variation_m=result.trunk_variation_m,
        thigh_tolerance_m=result.thigh_tolerance_m,
        shank_tolerance_m=result.shank_tolerance_m,
        trunk_tolerance_m=result.trunk_tolerance_m,
        window_duration_s=result.window_duration_s,
        thigh_passed=result.thigh_passed,
        shank_passed=result.shank_passed,
        trunk_passed=result.trunk_passed,
        overall_passed=result.gate_passed,
    )

    if result.gate_passed:
        response = CalibrationResponse(
            session_id=body.session_id,
            status="LOCKED",
            scale_m_per_px=result.scale_m_per_px,
            segments_m=LockedSegments(
                thigh_m=result.thigh_m,
                shank_m=result.shank_m,
                trunk_m=result.trunk_m,
                leg_m=result.leg_m,
            ),
            stability_check=stability_result,
            frames_used=result.frames_used,
            error=None,
        )
        return ok(data=response.model_dump(), message="Calibration locked successfully.")
    else:
        gate_status = (
            "INSUFFICIENT_DATA" if result.frames_used < 120 else "FAILED"
        )
        response = CalibrationResponse(
            session_id=body.session_id,
            status=gate_status,
            scale_m_per_px=None,
            segments_m=None,
            stability_check=stability_result,
            frames_used=result.frames_used,
            error=result.error_message,
        )
        return ok(
            data=response.model_dump(),
            message=f"Calibration {gate_status.lower().replace('_', ' ')}.",
        )