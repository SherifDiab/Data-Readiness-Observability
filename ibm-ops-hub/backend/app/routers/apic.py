"""API Connect router — GET /api/apic/logs, GET /api/apic/summary"""

from fastapi import APIRouter, HTTPException, Query

from app.polling.scheduler import get_apic_service
from app.schemas import ApiCallLog, ApicSummary

router = APIRouter()


@router.get("/logs", response_model=list[ApiCallLog])
async def get_logs(
    timeframe: str = Query("last1hour"),
    api_name: str | None = Query(None),
    status_code: int | None = Query(None),
):
    svc = get_apic_service()
    if not svc:
        raise HTTPException(503, "APIC service not initialized")
    logs, _ = await svc.get_logs_cached(timeframe)

    if api_name:
        logs = [l for l in logs if api_name.lower() in l.api_name.lower()]
    if status_code:
        logs = [l for l in logs if l.status_code == status_code]

    return logs


@router.get("/summary", response_model=ApicSummary)
async def get_summary(timeframe: str = Query("last1hour")):
    svc = get_apic_service()
    if not svc:
        raise HTTPException(503, "APIC service not initialized")
    _, summary = await svc.get_logs_cached(timeframe)
    return summary
