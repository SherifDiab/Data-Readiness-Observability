"""Spark Jobs router — GET /api/spark/jobs"""

from fastapi import APIRouter, HTTPException

from app.polling.scheduler import get_spark_service
from app.schemas import NormalizedJob

router = APIRouter()


@router.get("/jobs", response_model=list[NormalizedJob])
async def list_spark_jobs():
    """Return cached Spark job statuses. Falls back to live poll if cache is empty."""
    svc = get_spark_service()
    if not svc:
        raise HTTPException(503, "Spark service not initialized")
    cached = await svc.get_cached("spark:jobs")
    if cached is not None:
        return [NormalizedJob(**j) for j in cached]
    jobs = await svc.poll()
    return jobs


@router.get("/jobs/{job_id}", response_model=NormalizedJob)
async def get_spark_job(job_id: str):
    """Return a single Spark job by ID."""
    svc = get_spark_service()
    if not svc:
        raise HTTPException(503, "Spark service not initialized")
    cached = await svc.get_cached("spark:jobs")
    if cached:
        for j in cached:
            if j.get("job_id") == job_id:
                return NormalizedJob(**j)
    raise HTTPException(404, f"Job {job_id} not found")
