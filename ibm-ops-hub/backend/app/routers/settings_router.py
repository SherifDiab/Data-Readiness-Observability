"""Settings router — GET /api/settings, POST /api/settings/refresh/{component}"""

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.polling.scheduler import trigger_poll

router = APIRouter()


@router.get("")
async def get_settings():
    """Return non-sensitive configuration and polling intervals."""
    return {
        "polling_intervals": {
            "spark": settings.SPARK_POLL_INTERVAL,
            "datastage": settings.DATASTAGE_POLL_INTERVAL,
            "flink": settings.FLINK_POLL_INTERVAL,
            "event_processing": settings.EVENT_PROCESSING_POLL_INTERVAL,
            "apic": settings.APIC_POLL_INTERVAL,
        },
        "mock_mode": settings.MOCK_MODE,
        "enable_alerting": settings.ENABLE_ALERTING,
        "k8s_namespace": settings.K8S_NAMESPACE,
        "apic_org": settings.APIC_ORG,
        "apic_catalog": settings.APIC_CATALOG,
    }


@router.post("/refresh/{component}")
async def force_refresh(component: str):
    """Force immediate re-poll of a specific component."""
    valid = {"spark", "datastage", "flink", "event_processing", "apic"}
    if component not in valid:
        raise HTTPException(400, f"Invalid component. Must be one of: {', '.join(valid)}")
    await trigger_poll(component)
    return {"status": "triggered", "component": component}
