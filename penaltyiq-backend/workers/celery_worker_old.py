import os
import json
import logging
from celery import Celery
from celery.exceptions import MaxRetriesExceededError
from services.job_manager import JobManager
from core.pipeline.extractor import extract_frames, get_video_metadata
from core.pipeline.calibration import run_auto_calibration, LockedCalibration, LockedSegments
from core.pipeline.validation import validate_calibration_override
from core.pipeline.physics import run_physics
from core.pipeline.ik import run_ik
from core.pipeline.coaching import generate_coaching
from storage.file_system import get_video_path

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

app = Celery('penaltyiq_workers', broker=REDIS_URL)
app.conf.update(
    task_time_limit=120,
    task_soft_time_limit=100
)

job_manager = JobManager(REDIS_URL)

def safe_update_job(job_id: str, data: dict):
    try:
        job_manager.update_job(job_id, data)
    except Exception as e:
        logger.error(f"Failed to update job {job_id} in Redis: {str(e)}")

@app.task(bind=True, max_retries=1)
def process_video_task(self, job_id: str, goal_zone: str, calibration_override: str = None):
    pipeline_warnings = []
    logger.info(f"Starting job {job_id}...")
    try:
        safe_update_job(job_id, {"status": "extracting", "progress": 10})
        video_path = get_video_path(job_id)

        if not os.path.exists(video_path):
            raise ValueError(f"Video file not found at path: {video_path}")
        
        frames = extract_frames(video_path)
        metadata = get_video_metadata(video_path) 
        
        # 1. METADATA SAFETY CHECK
        if not isinstance(metadata, dict) or "width" not in metadata or "height" not in metadata:
            raise ValueError("Calibration failed: Video metadata (width/height) unavailable.")
            
        if not frames:
            raise ValueError("Extraction Failed: No valid human or ball targets tracked.")

        if len(frames) > 300:
            logger.warning(f"Job {job_id}: Truncating frames from {len(frames)} to 300 using smart sampling to protect memory.")
            indices = [int(i) for i in (x * (len(frames) - 1) / 299 for x in range(300))]
            frames = [frames[i] for i in indices]
            pipeline_warnings.append("Video sampled to 300 frames. Processing using smart sampling.")
        
        safe_update_job(job_id, {"status": "calibrating", "progress": 30})
        
        # --- CALIBRATION ROUTING ---
        if calibration_override:
            try:
                calib_dict = json.loads(calibration_override)
            except json.JSONDecodeError:
                raise ValueError("Manual calibration override contains invalid JSON.")
            
            required_keys = ["scale_m_per_px", "segments_m"]
            for key in required_keys:
                if key not in calib_dict:
                    raise ValueError("Invalid calibration override schema: missing required keys.")

            if not validate_calibration_override(calib_dict):
                raise ValueError("Manual calibration override failed biological validation limits.")
                
            segs_dict = calib_dict["segments_m"]
            segments = LockedSegments(
                thigh_m=segs_dict["thigh_m"], shank_m=segs_dict["shank_m"],
                trunk_m=segs_dict["trunk_m"], leg_m=segs_dict["leg_m"]
            )
            calibration = LockedCalibration(
                scale_m_per_px=calib_dict["scale_m_per_px"], 
                segments_m=segments,
                confidence_score=1.0, 
                pipeline_warnings=[]
            )
        else:
            # Auto-calibration using required width/height fields
            calibration = run_auto_calibration(frames, metadata["width"], metadata["height"])

        pipeline_warnings.extend(calibration.pipeline_warnings)
        pipeline_warnings = list(set(pipeline_warnings))
        if pipeline_warnings:
            logger.warning(f"Job {job_id} calibration warnings: {pipeline_warnings}")

        logger.info(f"[JOB {job_id}] Stage: calibration | Confidence: {calibration.confidence_score}")

        safe_update_job(job_id, {"status": "physics", "progress": 60})
        
        # --- ANALYSIS EXECUTION ---
        physics_data = run_physics(frames, calibration)
        if physics_data is None or len(physics_data) == 0:
            raise ValueError("Physics Engine Failed: No data returned.")

        safe_update_job(job_id, {"status": "ik", "progress": 80})
        ik_data = run_ik(frames, calibration)
        if ik_data is None or len(ik_data) == 0:
            raise ValueError("Inverse Kinematics Failed: No data returned.")

        safe_update_job(job_id, {"status": "coaching", "progress": 90})
        coaching_data = generate_coaching(physics_data, ik_data)
        
        # 5. DYNAMIC WARNING PASSTHROUGH & FRONTEND EXPOSURE
        result = {
            "status": "success",
            "pipeline_warnings": pipeline_warnings,
            "calibration_confidence": calibration.confidence_score, 
            "coaching_alerts": coaching_data,
            "physics_results": physics_data,
            "ik_results": ik_data,
            "scores": {"overall": 85.0, "power": 88.0, "technique": 82.0}
        }
        
        safe_update_job(job_id, {"status": "completed", "progress": 100, "result": result})
        logger.info(f"Successfully completed job {job_id}.")

    # FATAL ERROR SAFETY NET
    except ValueError as ve:
        logger.error(f"Job {job_id} failed with ValueError: {str(ve)}")
        safe_update_job(job_id, {"status": "failed", "progress": 0, "error": str(ve)})
    except Exception as e:
        if "Redis" in str(e) or "Connection" in str(e) or "Timeout" in str(e):
            logger.error(f"Job {job_id} experienced transient error: {str(e)}. Retrying...")
            try:
                self.retry(exc=e, countdown=5)
            except MaxRetriesExceededError:
                logger.error(f"Job {job_id} exceeded max retries. Marking as failed.")
                safe_update_job(job_id, {"status": "failed", "progress": 0, "error": f"Internal System Error (Transient): {str(e)}"})
        else:
            logger.error(f"Job {job_id} experienced fatal error: {str(e)}.")
            safe_update_job(job_id, {"status": "failed", "progress": 0, "error": f"Internal System Error: {str(e)}"})