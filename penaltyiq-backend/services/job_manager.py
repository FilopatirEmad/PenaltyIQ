import json
import redis
import logging

logger = logging.getLogger(__name__)

class JobManager:
    def __init__(self, redis_url: str):
        self.redis_client = redis.Redis.from_url(redis_url, decode_responses=True)

    def update_job(self, job_id: str, data: dict):
        try:
            current = self.get_job(job_id) or {}
            current.update(data)
            self.redis_client.set(f"job:{job_id}", json.dumps(current), ex=86400)
        except Exception as e:
            logger.error(f"Failed to update job {job_id}: {e}")

    def get_job(self, job_id: str) -> dict:
        try:
            data = self.redis_client.get(f"job:{job_id}")
            return json.loads(data) if data else None
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return None
