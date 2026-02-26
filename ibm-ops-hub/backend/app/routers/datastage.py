"""DataStage Jobs router — GET /api/datastage/jobs"""

from fastapi import APIRouter, HTTPException

from app.polling.scheduler import get_datastage_service
from app.schemas import NormalizedJob

router = APIRouter()


@router.get("/jobs", response_model=list[NormalizedJob])
async def list_datastage_jobs():
    svc = get_datastage_service()
    if not svc:
        raise HTTPException(503, "DataStage service not initialized")
    cached = await svc.get_cached("datastage:jobs")
    if cached is not None:
        return [NormalizedJob(**j) for j in cached]
    return await svc.poll()


@router.get("/jobs/{job_id}", response_model=NormalizedJob)
async def get_datastage_job(job_id: str):
    svc = get_datastage_service()
    if not svc:
        raise HTTPException(503, "DataStage service not initialized")
    cached = await svc.get_cached("datastage:jobs")
    if cached:
        for j in cached:
            if j.get("job_id") == job_id:
                return NormalizedJob(**j)
    raise HTTPException(404, f"Job {job_id} not found")
