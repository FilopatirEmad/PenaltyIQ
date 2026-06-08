import uuid
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException

from services.job_manager import JobManager
from workers.celery_worker import process_video_task
from storage.file_system import save_video
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

router = APIRouter(prefix="/api/v2", tags=["v2_async"])
job_manager = JobManager(REDIS_URL)

@router.post("/process-video-async")
async def process_video_async(
    video: UploadFile = File(...),
    goal_zone: str = Form(...),
    calibration_override: Optional[str] = Form(None)
):
    try:
        job_id = str(uuid.uuid4())
        
        # Initialize job state
        job_manager.update_job(job_id, {"status": "queued", "progress": 0})
        
        # Save video to shared storage (local or S3)
        video_bytes = await video.read()
        save_video(job_id, video_bytes)
        
        # Push task to Celery queue
        process_video_task.delay(job_id, goal_zone, calibration_override)
        
        return {
            "job_id": job_id,
            "status": "queued"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to queue job: {str(e)}")

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "status": job.get("status", "unknown"),
        "progress": job.get("progress", 0)
    }

@router.get("/result/{job_id}")
async def get_job_result(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    status = job.get("status")
    
    if status == "failed":
        raise HTTPException(status_code=400, detail=f"Job failed: {job.get('error')}")
        
    if status != "completed":
        # 425 Too Early indicates the resource is not ready yet
        raise HTTPException(status_code=425, detail="Job is not yet completed")
        
    return job.get("result", {})
