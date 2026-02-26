"""
Utilities for normalizing job data from various IBM services into the common schema.
"""

from datetime import datetime, timezone

from app.schemas import ComponentHealth, ComponentType, JobStatus, NormalizedJob


def compute_health(component: ComponentType, jobs: list[NormalizedJob], is_reachable: bool = True, error_message: str | None = None) -> ComponentHealth:
    """Compute aggregated health metrics from a list of normalized jobs."""
    running = sum(1 for j in jobs if j.status == JobStatus.RUNNING)
    completed = sum(1 for j in jobs if j.status == JobStatus.COMPLETED)
    failed = sum(1 for j in jobs if j.status == JobStatus.FAILED)
    warning = sum(1 for j in jobs if j.status == JobStatus.WARNING)
    other = len(jobs) - running - completed - failed - warning

    return ComponentHealth(
        component=component,
        total_jobs=len(jobs),
        running=running,
        completed=completed,
        failed=failed,
        warning=warning,
        other=other,
        last_polled_at=datetime.now(timezone.utc),
        is_reachable=is_reachable,
        error_message=error_message,
    )


def epoch_ms_to_datetime(epoch_ms: int | None) -> datetime | None:
    """Convert epoch milliseconds to a timezone-aware datetime."""
    if epoch_ms is None or epoch_ms < 0:
        return None
    return datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
