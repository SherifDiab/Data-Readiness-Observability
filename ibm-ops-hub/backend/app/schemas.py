"""
Pydantic schemas for normalized job data across all IBM components.
All five services normalize their data into these common formats.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel


class JobStatus(str, Enum):
    RUNNING = "Running"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELED = "Canceled"
    QUEUED = "Queued"
    STARTING = "Starting"
    WARNING = "Warning"
    SUSPENDED = "Suspended"
    RESTARTING = "Restarting"
    UNKNOWN = "Unknown"


class ComponentType(str, Enum):
    SPARK = "spark"
    DATASTAGE = "datastage"
    EVENT_PROCESSING = "event_processing"
    FLINK = "flink"
    APIC = "apic"


class NormalizedJob(BaseModel):
    component: ComponentType
    job_id: str
    job_name: str
    status: JobStatus
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_seconds: float | None = None
    details: dict[str, Any] = {}
    native_url: str | None = None
    last_polled_at: datetime


class ComponentHealth(BaseModel):
    component: ComponentType
    total_jobs: int
    running: int
    completed: int
    failed: int
    warning: int
    other: int
    last_polled_at: datetime
    is_reachable: bool
    error_message: str | None = None


class DashboardSummary(BaseModel):
    components: list[ComponentHealth]
    total_failures: int
    critical_alerts: list[str]
    last_updated: datetime


class ApiCallLog(BaseModel):
    timestamp: datetime
    api_name: str
    path: str
    method: str
    status_code: int
    latency_ms: float
    client_ip: str | None = None
    consumer_org: str | None = None


class ApicSummary(BaseModel):
    total_calls: int
    success_count: int
    error_count: int
    avg_latency_ms: float
    p95_latency_ms: float
    error_rate_percent: float
    top_errors: list[dict[str, Any]]
    calls_by_minute: list[dict[str, Any]]
    timeframe: str


class FlinkClusterOverview(BaseModel):
    taskmanagers: int
    slots_total: int
    slots_available: int
    jobs_running: int
    jobs_finished: int
    jobs_cancelled: int
    jobs_failed: int
    flink_version: str
