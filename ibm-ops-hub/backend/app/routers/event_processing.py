"""Event Processing router — GET /api/event-processing/flows"""

from fastapi import APIRouter, HTTPException

from app.polling.scheduler import get_event_processing_service
from app.schemas import NormalizedJob

router = APIRouter()


@router.get("/flows", response_model=list[NormalizedJob])
async def list_flows():
    svc = get_event_processing_service()
    if not svc:
        raise HTTPException(503, "Event Processing service not initialized")
    cached = await svc.get_cached("event_processing:flows")
    if cached is not None:
        return [NormalizedJob(**j) for j in cached]
    return await svc.poll()


@router.get("/flows/{flow_id}", response_model=NormalizedJob)
async def get_flow(flow_id: str):
    svc = get_event_processing_service()
    if not svc:
        raise HTTPException(503, "Event Processing service not initialized")
    cached = await svc.get_cached("event_processing:flows")
    if cached:
        for j in cached:
            if j.get("job_id") == flow_id:
                return NormalizedJob(**j)
    raise HTTPException(404, f"Flow {flow_id} not found")
