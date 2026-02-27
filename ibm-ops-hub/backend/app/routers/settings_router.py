"""
Settings router — full CRUD for runtime configuration.

GET  /api/settings           → all settings grouped by category (sensitive fields masked)
GET  /api/settings/schema    → field definitions only (no values)
PUT  /api/settings           → apply partial overrides; persisted to Redis
POST /api/settings/refresh/{component} → force immediate re-poll
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.polling.scheduler import trigger_poll
from app.settings_store import SETTINGS_SCHEMA, get_all_settings, update_settings

router = APIRouter()


class SettingsUpdateRequest(BaseModel):
    changes: dict[str, str | int | bool | None]


@router.get("")
async def get_settings_endpoint():
    """Return all settings grouped by category, with sensitive fields masked."""
    return await get_all_settings()


@router.get("/schema")
async def get_settings_schema():
    """Return only the field schema (labels, types, hints) without values."""
    return {"schema": SETTINGS_SCHEMA}


@router.put("")
async def update_settings_endpoint(body: SettingsUpdateRequest):
    """Apply a partial set of setting overrides and persist to Redis.

    Sensitive fields are only updated when a non-empty, non-placeholder value
    is provided. Returns which keys were applied vs skipped.
    """
    # Filter out explicit nulls — client sends null for fields it didn't touch
    changes = {k: v for k, v in body.changes.items() if v is not None}
    result = await update_settings(changes)
    return {
        "status": "ok",
        "applied": result["applied"],
        "skipped": result["skipped"],
    }


@router.post("/refresh/{component}")
async def force_refresh(component: str):
    """Force immediate re-poll of a specific component."""
    valid = {"spark", "datastage", "flink", "event_processing", "apic"}
    if component not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid component. Must be one of: {', '.join(sorted(valid))}",
        )
    await trigger_poll(component)
    return {"status": "triggered", "component": component}
