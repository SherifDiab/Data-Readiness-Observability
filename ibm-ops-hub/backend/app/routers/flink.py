"""Flink Jobs router — GET /api/flink/jobs, GET /api/flink/cluster"""

from fastapi import APIRouter, HTTPException

from app.polling.scheduler import get_flink_service
from app.schemas import FlinkClusterOverview, NormalizedJob

router = APIRouter()


@router.get("/jobs", response_model=list[NormalizedJob])
async def list_flink_jobs():
    svc = get_flink_service()
    if not svc:
        raise HTTPException(503, "Flink service not initialized")
    cached = await svc.get_cached("flink:jobs")
    if cached is not None:
        return [NormalizedJob(**j) for j in cached]
    return await svc.poll()


@router.get("/cluster", response_model=FlinkClusterOverview)
async def get_cluster():
    svc = get_flink_service()
    if not svc:
        raise HTTPException(503, "Flink service not initialized")
    return await svc.get_cluster_overview()


@router.get("/jobs/{jid}", response_model=NormalizedJob)
async def get_flink_job(jid: str):
    svc = get_flink_service()
    if not svc:
        raise HTTPException(503, "Flink service not initialized")
    cached = await svc.get_cached("flink:jobs")
    if cached:
        for j in cached:
            if j.get("job_id") == jid:
                return NormalizedJob(**j)
    raise HTTPException(404, f"Flink job {jid} not found")
