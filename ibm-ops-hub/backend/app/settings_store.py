"""
Runtime settings store — persists configuration overrides in Redis so they
survive backend restarts and are applied immediately without redeployment.

Design
------
- The canonical defaults come from environment variables (via config.Settings).
- Overrides written via PUT /api/settings are stored as a JSON dict at Redis
  key ``"settings:overrides"``.
- On every read, the store merges env-var values with Redis overrides
  (overrides win).
- Sensitive fields (passwords, tokens) are never returned in GET responses;
  a non-empty incoming value replaces the stored one, an empty string is ignored.
- After saving, the module-level ``settings`` singleton is updated in-place so
  running pollers pick up the new values on their next cycle.
"""

import json
import logging
from typing import Any

from app.cache import get_redis
from app.config import settings

logger = logging.getLogger(__name__)

REDIS_KEY = "settings:overrides"

# Fields never returned in GET responses
SENSITIVE_FIELDS = {"CPD_PASSWORD", "IIS_PASSWORD", "APIC_PASSWORD", "SLACK_WEBHOOK_URL"}

# All configurable fields grouped by category for the UI
SETTINGS_SCHEMA: dict[str, list[dict[str, Any]]] = {
    "cpd": [
        {"key": "CPD_BASE_URL",      "label": "CPD Base URL",         "type": "url",      "required": True},
        {"key": "CPD_USERNAME",      "label": "Username",             "type": "text",     "required": True},
        {"key": "CPD_PASSWORD",      "label": "Password",             "type": "password", "required": True,  "sensitive": True},
        {"key": "CPD_PROJECT_IDS",   "label": "Project IDs",          "type": "tags",     "required": False,
         "hint": "Comma-separated list of CPD project IDs to monitor (e.g. proj-analytics,proj-finance). Leave empty to use the single Project ID below."},
        {"key": "CPD_PROJECT_ID",    "label": "Single Project ID",    "type": "text",     "required": False,
         "hint": "Used only when Project IDs above is empty."},
    ],
    "datastage": [
        {"key": "DATASTAGE_USE_CPD", "label": "Use CPD API",          "type": "boolean",  "required": False,
         "hint": "When enabled, DataStage jobs are polled via the CPD Jobs API (same credentials as Spark). Disable to use the IIS REST API."},
        {"key": "IIS_BASE_URL",      "label": "IIS Base URL",         "type": "url",      "required": False},
        {"key": "IIS_USERNAME",      "label": "IIS Username",         "type": "text",     "required": False},
        {"key": "IIS_PASSWORD",      "label": "IIS Password",         "type": "password", "required": False, "sensitive": True},
    ],
    "flink": [
        {"key": "FLINK_REST_URL",    "label": "Flink REST URL",       "type": "url",      "required": True,
         "hint": "Flink JobManager REST API (default port 8081). e.g. http://flink-jobmanager:8081"},
        {"key": "FLINK_CLUSTERS",    "label": "Additional Clusters",  "type": "text",     "required": False,
         "hint": "Comma-separated list of additional Flink cluster URLs to monitor."},
    ],
    "event_processing": [
        {"key": "K8S_NAMESPACE",     "label": "K8s Namespace",        "type": "text",     "required": True,
         "hint": "Kubernetes namespace containing FlinkDeployment CRDs (e.g. event-automation)."},
        {"key": "K8S_IN_CLUSTER",    "label": "In-Cluster Auth",      "type": "boolean",  "required": False,
         "hint": "Enable when the backend runs inside the same Kubernetes cluster. Disable to use a kubeconfig file."},
        {"key": "K8S_KUBECONFIG",    "label": "Kubeconfig Path",      "type": "text",     "required": False,
         "hint": "Absolute path to kubeconfig file. Only used when In-Cluster Auth is disabled."},
    ],
    "apic": [
        {"key": "APIC_MGMT_URL",     "label": "Management URL",       "type": "url",      "required": True},
        {"key": "APIC_ANALYTICS_URL","label": "Analytics URL",        "type": "url",      "required": True},
        {"key": "APIC_ORG",          "label": "Provider Org",         "type": "text",     "required": True},
        {"key": "APIC_CATALOG",      "label": "Catalog",              "type": "text",     "required": True},
        {"key": "APIC_REALM",        "label": "Realm",                "type": "text",     "required": False,
         "hint": "Default: provider/default-idp-2"},
        {"key": "APIC_USERNAME",     "label": "Username",             "type": "text",     "required": True},
        {"key": "APIC_PASSWORD",     "label": "Password",             "type": "password", "required": True,  "sensitive": True},
    ],
    "polling": [
        {"key": "SPARK_POLL_INTERVAL",            "label": "Spark Interval (s)",            "type": "number", "min": 10,  "max": 300},
        {"key": "DATASTAGE_POLL_INTERVAL",        "label": "DataStage Interval (s)",        "type": "number", "min": 10,  "max": 300},
        {"key": "FLINK_POLL_INTERVAL",            "label": "Flink Interval (s)",            "type": "number", "min": 5,   "max": 300},
        {"key": "EVENT_PROCESSING_POLL_INTERVAL", "label": "Event Processing Interval (s)", "type": "number", "min": 10,  "max": 300},
        {"key": "APIC_POLL_INTERVAL",             "label": "API Connect Interval (s)",      "type": "number", "min": 30,  "max": 600},
    ],
    "general": [
        {"key": "MOCK_MODE",         "label": "Mock Mode",            "type": "boolean",
         "hint": "Point all services at the local mock server instead of real IBM APIs."},
        {"key": "MOCK_SERVER_URL",   "label": "Mock Server URL",      "type": "url",
         "hint": "Base URL of the mock server (used only when Mock Mode is enabled)."},
        {"key": "ENABLE_ALERTING",   "label": "Enable Alerting",      "type": "boolean",
         "hint": "Send Slack notifications when jobs fail."},
        {"key": "SLACK_WEBHOOK_URL", "label": "Slack Webhook URL",    "type": "password", "sensitive": True,
         "hint": "Incoming webhook URL for Slack failure notifications."},
    ],
}


async def _load_overrides() -> dict[str, Any]:
    """Load persisted overrides from Redis."""
    try:
        r = get_redis()
        raw = await r.get(REDIS_KEY)
        if raw:
            return json.loads(raw)
    except Exception as exc:
        logger.warning("Could not load settings overrides from Redis: %s", exc)
    return {}


async def _save_overrides(overrides: dict[str, Any]) -> None:
    """Persist overrides to Redis."""
    try:
        r = get_redis()
        await r.set(REDIS_KEY, json.dumps(overrides))
    except Exception as exc:
        logger.error("Could not save settings overrides to Redis: %s", exc)


def _current_value(key: str) -> Any:
    """Read the live value from the in-memory settings singleton."""
    return getattr(settings, key, None)


def _apply_to_settings(key: str, value: Any) -> None:
    """Apply a single override to the in-memory settings singleton."""
    try:
        current = getattr(settings, key)
        if isinstance(current, bool):
            if isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            else:
                value = bool(value)
        elif isinstance(current, int):
            value = int(value)
        object.__setattr__(settings, key, value)
        logger.info("Settings updated: %s = %r", key, value if key not in SENSITIVE_FIELDS else "***")
    except Exception as exc:
        logger.warning("Could not apply setting %s: %s", key, exc)


async def get_all_settings() -> dict[str, Any]:
    """Return all settings grouped by category, with sensitive fields masked."""
    overrides = await _load_overrides()

    result: dict[str, Any] = {"schema": SETTINGS_SCHEMA, "values": {}, "overrides": list(overrides.keys())}

    all_keys = {f["key"] for cat in SETTINGS_SCHEMA.values() for f in cat}
    for key in all_keys:
        if key in SENSITIVE_FIELDS:
            # Return a sentinel so the UI knows a value is set without revealing it
            live = _current_value(key)
            result["values"][key] = "••••••••" if live else ""
        else:
            result["values"][key] = _current_value(key)

    return result


async def update_settings(changes: dict[str, Any]) -> dict[str, list[str]]:
    """Apply and persist a dict of setting key→value pairs.

    Sensitive fields are only updated when a non-empty, non-placeholder value
    is provided. Returns a summary of applied and skipped keys.
    """
    overrides = await _load_overrides()
    applied: list[str] = []
    skipped: list[str] = []

    valid_keys = {f["key"] for cat in SETTINGS_SCHEMA.values() for f in cat}

    for key, value in changes.items():
        if key not in valid_keys:
            logger.warning("Unknown settings key ignored: %s", key)
            skipped.append(key)
            continue

        if key in SENSITIVE_FIELDS:
            # Skip empty or placeholder values (user didn't change the password)
            if not value or value == "••••••••":
                skipped.append(key)
                continue

        _apply_to_settings(key, value)
        overrides[key] = value
        applied.append(key)

    await _save_overrides(overrides)
    return {"applied": applied, "skipped": skipped}


async def load_overrides_on_startup() -> None:
    """Called at app startup to restore any previously saved overrides."""
    overrides = await _load_overrides()
    if not overrides:
        return
    for key, value in overrides.items():
        _apply_to_settings(key, value)
    logger.info("Restored %d settings override(s) from Redis: %s", len(overrides), list(overrides.keys()))
