"""Dashboard router — aggregated health view of all 5 components."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app.polling.scheduler import (
    get_apic_service,
    get_datastage_service,
    get_event_processing_service,
    get_flink_service,
    get_spark_service,
)
from app.schemas import ComponentHealth, ComponentType, DashboardSummary, JobStatus, NormalizedJob
from app.utils.normalize import compute_health

router = APIRouter()


async def _get_all_health() -> list[ComponentHealth]:
    results = []

    services = [
        ("spark", get_spark_service(), "spark:jobs", ComponentType.SPARK),
        ("datastage", get_datastage_service(), "datastage:jobs", ComponentType.DATASTAGE),
        ("event_processing", get_event_processing_service(), "event_processing:flows", ComponentType.EVENT_PROCESSING),
        ("flink", get_flink_service(), "flink:jobs", ComponentType.FLINK),
    ]

    for name, svc, cache_key, comp_type in services:
        if svc is None:
            results.append(ComponentHealth(
                component=comp_type, total_jobs=0, running=0, completed=0, failed=0,
                warning=0, other=0, last_polled_at=datetime.now(timezone.utc),
                is_reachable=False, error_message="Service not initialized",
            ))
            continue
        try:
            cached = await svc.get_cached(cache_key)
            if cached:
                jobs = [NormalizedJob(**j) for j in cached]
                health = compute_health(comp_type, jobs)
            else:
                health = compute_health(comp_type, [], is_reachable=False, error_message="No cached data")
            results.append(health)
        except Exception as e:
            results.append(ComponentHealth(
                component=comp_type, total_jobs=0, running=0, completed=0, failed=0,
                warning=0, other=0, last_polled_at=datetime.now(timezone.utc),
                is_reachable=False, error_message=str(e),
            ))

    # APIC health
    apic_svc = get_apic_service()
    if apic_svc:
        try:
            health = await apic_svc.get_health()
            results.append(health)
        except Exception as e:
            results.append(ComponentHealth(
                component=ComponentType.APIC, total_jobs=0, running=0, completed=0, failed=0,
                warning=0, other=0, last_polled_at=datetime.now(timezone.utc),
                is_reachable=False, error_message=str(e),
            ))
    else:
        results.append(ComponentHealth(
            component=ComponentType.APIC, total_jobs=0, running=0, completed=0, failed=0,
            warning=0, other=0, last_polled_at=datetime.now(timezone.utc),
            is_reachable=False, error_message="Service not initialized",
        ))

    return results


@router.get("/summary", response_model=DashboardSummary)
async def get_summary():
    components = await _get_all_health()
    total_failures = sum(c.failed for c in components)
    critical_alerts = [
        f"{c.component.value}: {c.failed} failed job(s)"
        for c in components
        if c.failed > 0
    ]

    return DashboardSummary(
        components=components,
        total_failures=total_failures,
        critical_alerts=critical_alerts,
        last_updated=datetime.now(timezone.utc),
    )


@router.get("/health", response_model=list[ComponentHealth])
async def get_health():
    return await _get_all_health()
