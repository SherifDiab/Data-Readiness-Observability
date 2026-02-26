"""
Mock Flink REST API
===================
Simulates the Apache Flink REST API endpoints.
- GET /overview                    -> cluster summary
- GET /jobs/overview               -> list of Flink jobs
- GET /jobs/{jid}/exceptions       -> root exception for failed jobs
- GET /jobs/{jid}/checkpoints      -> checkpoint info for running jobs
"""

import hashlib
import random
import time
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter

router = APIRouter()

BASE_SEED = 123

FLINK_STATES = [
    "CREATED",
    "RUNNING",
    "FAILING",
    "FAILED",
    "CANCELLING",
    "CANCELED",
    "FINISHED",
    "RESTARTING",
    "SUSPENDED",
    "RECONCILING",
]

# Weighted distribution: mostly RUNNING and FINISHED
FLINK_STATE_WEIGHTS = [
    3,   # CREATED
    40,  # RUNNING
    3,   # FAILING
    8,   # FAILED
    2,   # CANCELLING
    5,   # CANCELED
    30,  # FINISHED
    3,   # RESTARTING
    3,   # SUSPENDED
    3,   # RECONCILING
]

FLINK_JOB_NAMES = [
    "ClickstreamAggregator",
    "FraudDetectionPipeline",
    "RealTimeRecommendation",
    "OrderEventProcessor",
    "PaymentStreamValidator",
    "InventoryLevelMonitor",
    "UserSessionAnalytics",
    "LogAnomalyDetector",
    "PriceUpdateBroadcast",
    "ShipmentTrackingEnricher",
    "CustomerEventCorrelator",
    "IoTSensorAggregation",
    "MarketDataStreamProcessor",
    "NotificationDispatcher",
    "SearchIndexUpdater",
    "MetricsRollupPipeline",
    "CDCDatabaseReplicator",
    "GeofenceAlertProcessor",
    "SocialFeedAnalyzer",
    "VideoTranscodingOrchestrator",
    "AdImpressionCounter",
    "RiskScoringStream",
    "CacheInvalidationPropagator",
    "AuditTrailWriter",
    "DataQualityStreamMonitor",
]


def _deterministic_jid(seed_str: str) -> str:
    """Generate a 32-char hex job ID (Flink style)."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return h[:32]


def _time_based_state(job_idx: int) -> str:
    """
    Determine job state based on current time and job index.
    Most jobs stay in their seeded state but a few cycle.
    """
    rng = random.Random(BASE_SEED + job_idx)
    base_state = rng.choices(FLINK_STATES, weights=FLINK_STATE_WEIGHTS, k=1)[0]

    # ~30% of jobs cycle states over time
    if job_idx % 3 == 0:
        now_seconds = int(time.time())
        cycle_period = 45 + (job_idx * 9)
        cycle_offset = (now_seconds // cycle_period) % len(FLINK_STATES)
        # Weighted towards RUNNING and FINISHED even when cycling
        cycling_states = ["RUNNING", "RUNNING", "FINISHED", "RUNNING", "FAILED",
                          "RESTARTING", "RUNNING", "RUNNING", "FINISHED", "RUNNING"]
        return cycling_states[cycle_offset % len(cycling_states)]

    return base_state


def _generate_flink_jobs():
    """Generate list of mock Flink jobs."""
    now_ms = int(time.time() * 1000)
    rng = random.Random(BASE_SEED)
    jobs = []

    for idx, name in enumerate(FLINK_JOB_NAMES):
        jid = _deterministic_jid(f"flink-job-{idx}")
        state = _time_based_state(idx)

        # Start time: somewhere in the last 7 days
        start_offset_ms = rng.randint(1_000, 7 * 24 * 3600 * 1000)
        start_time = now_ms - start_offset_ms

        # Duration and end-time depend on state
        if state in ("FINISHED", "FAILED", "CANCELED"):
            duration_ms = rng.randint(5_000, 3_600_000)  # 5s to 1h
            end_time = start_time + duration_ms
        else:
            # Still running or transitional
            duration_ms = now_ms - start_time
            end_time = -1

        last_modification = now_ms - rng.randint(0, 60_000)

        # Task breakdown
        total_tasks = rng.choice([4, 8, 12, 16, 24, 32])
        if state == "RUNNING":
            tasks = {
                "total": total_tasks,
                "created": 0,
                "scheduled": 0,
                "deploying": 0,
                "running": total_tasks,
                "finished": 0,
                "canceling": 0,
                "canceled": 0,
                "failed": 0,
                "reconciling": 0,
                "initializing": 0,
            }
        elif state == "FINISHED":
            tasks = {
                "total": total_tasks,
                "created": 0,
                "scheduled": 0,
                "deploying": 0,
                "running": 0,
                "finished": total_tasks,
                "canceling": 0,
                "canceled": 0,
                "failed": 0,
                "reconciling": 0,
                "initializing": 0,
            }
        elif state == "FAILED":
            failed_count = rng.randint(1, max(1, total_tasks // 4))
            tasks = {
                "total": total_tasks,
                "created": 0,
                "scheduled": 0,
                "deploying": 0,
                "running": 0,
                "finished": total_tasks - failed_count,
                "canceling": 0,
                "canceled": 0,
                "failed": failed_count,
                "reconciling": 0,
                "initializing": 0,
            }
        elif state == "CREATED":
            tasks = {
                "total": total_tasks,
                "created": total_tasks,
                "scheduled": 0,
                "deploying": 0,
                "running": 0,
                "finished": 0,
                "canceling": 0,
                "canceled": 0,
                "failed": 0,
                "reconciling": 0,
                "initializing": 0,
            }
        elif state == "RESTARTING":
            init_count = rng.randint(1, total_tasks)
            tasks = {
                "total": total_tasks,
                "created": 0,
                "scheduled": 0,
                "deploying": 0,
                "running": 0,
                "finished": 0,
                "canceling": 0,
                "canceled": 0,
                "failed": 0,
                "reconciling": 0,
                "initializing": init_count,
            }
        else:
            # CANCELLING, SUSPENDED, RECONCILING, FAILING
            tasks = {
                "total": total_tasks,
                "created": 0,
                "scheduled": 0,
                "deploying": 0,
                "running": rng.randint(0, total_tasks),
                "finished": 0,
                "canceling": rng.randint(0, total_tasks // 2),
                "canceled": 0,
                "failed": 0,
                "reconciling": 0,
                "initializing": 0,
            }
            # Ensure tasks add up to total
            assigned = sum(tasks[k] for k in tasks if k != "total")
            diff = total_tasks - assigned
            if diff > 0:
                tasks["running"] += diff
            elif diff < 0:
                tasks["running"] = max(0, tasks["running"] + diff)

        jobs.append(
            {
                "jid": jid,
                "name": name,
                "state": state,
                "start-time": start_time,
                "end-time": end_time,
                "duration": duration_ms,
                "last-modification": last_modification,
                "tasks": tasks,
            }
        )

    return jobs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/overview")
async def cluster_overview():
    """Flink cluster summary."""
    now_seconds = int(time.time())
    rng = random.Random(BASE_SEED)

    jobs = _generate_flink_jobs()
    running = sum(1 for j in jobs if j["state"] == "RUNNING")
    finished = sum(1 for j in jobs if j["state"] == "FINISHED")
    cancelled = sum(1 for j in jobs if j["state"] == "CANCELED")
    failed = sum(1 for j in jobs if j["state"] == "FAILED")

    total_taskmanagers = rng.randint(4, 12)
    slots_per_tm = rng.choice([4, 8])
    total_slots = total_taskmanagers * slots_per_tm
    # Running jobs use some slots
    used_slots = min(total_slots, running * rng.randint(2, slots_per_tm))

    return {
        "taskmanagers": total_taskmanagers,
        "slots-total": total_slots,
        "slots-available": total_slots - used_slots,
        "jobs-running": running,
        "jobs-finished": finished,
        "jobs-cancelled": cancelled,
        "jobs-failed": failed,
        "flink-version": "1.18.1",
        "flink-commit": "a]b3c4d5e6f",
    }


@router.get("/jobs/overview")
async def jobs_overview():
    """List all Flink jobs with status overview."""
    jobs = _generate_flink_jobs()
    return {"jobs": jobs}


@router.get("/jobs/{jid}")
async def get_job_detail(jid: str):
    """Get detail for a single Flink job."""
    jobs = _generate_flink_jobs()
    for j in jobs:
        if j["jid"] == jid:
            return j
    return {"errors": [f"Job {jid} not found."]}


@router.get("/jobs/{jid}/exceptions")
async def get_job_exceptions(jid: str):
    """Return root exception for a Flink job (meaningful for FAILED jobs)."""
    jobs = _generate_flink_jobs()
    job = None
    job_idx = 0
    for i, j in enumerate(jobs):
        if j["jid"] == jid:
            job = j
            job_idx = i
            break

    if job is None:
        return {"errors": [f"Job {jid} not found."]}

    if job["state"] not in ("FAILED", "FAILING"):
        return {
            "root-exception": None,
            "timestamp": 0,
            "all-exceptions": [],
            "truncated": False,
        }

    rng = random.Random(f"{BASE_SEED}-exc-{jid}")

    exceptions = [
        {
            "exception": "org.apache.flink.runtime.JobException: Recovery is suppressed by NoRestartBackoffTimeStrategy",
            "task": f"Source: KafkaSource -> Map ({rng.randint(1,8)}/{rng.randint(8,16)})",
        },
        {
            "exception": "java.lang.OutOfMemoryError: Java heap space",
            "task": f"Window(TumblingProcessingTimeWindows(5000), ProcessWindowFunction) ({rng.randint(1,4)}/{rng.randint(4,8)})",
        },
        {
            "exception": "org.apache.flink.streaming.connectors.kafka.FlinkKafkaException: Failed to send data to Kafka: Topic not found",
            "task": f"Sink: KafkaSink ({rng.randint(1,4)}/{rng.randint(4,8)})",
        },
        {
            "exception": "java.io.IOException: Connection refused to downstream operator",
            "task": f"KeyedProcess -> Sink ({rng.randint(1,4)}/{rng.randint(4,8)})",
        },
        {
            "exception": "org.apache.flink.util.SerializedThrowable: Checkpoint was declined (task was not running)",
            "task": f"Source: KafkaSource ({rng.randint(1,4)}/{rng.randint(4,8)})",
        },
    ]

    selected = rng.choice(exceptions)
    now_ms = int(time.time() * 1000)

    return {
        "root-exception": selected["exception"],
        "timestamp": now_ms - rng.randint(1_000, 600_000),
        "all-exceptions": [
            {
                "exception": selected["exception"],
                "task": selected["task"],
                "location": f"taskmanager-{rng.randint(1,8)}.example.com:6122",
                "timestamp": now_ms - rng.randint(1_000, 600_000),
            }
        ],
        "truncated": False,
    }


@router.get("/jobs/{jid}/checkpoints")
async def get_job_checkpoints(jid: str):
    """Return checkpoint info for a Flink job."""
    jobs = _generate_flink_jobs()
    job = None
    job_idx = 0
    for i, j in enumerate(jobs):
        if j["jid"] == jid:
            job = j
            job_idx = i
            break

    if job is None:
        return {"errors": [f"Job {jid} not found."]}

    rng = random.Random(f"{BASE_SEED}-ckpt-{jid}")
    now_ms = int(time.time() * 1000)

    # Generate checkpoint history
    num_completed = rng.randint(5, 50)
    num_failed = rng.randint(0, 3)
    latest_ckpt_id = num_completed + num_failed

    # Generate recent checkpoint entries
    history = []
    for ckpt_idx in range(min(10, latest_ckpt_id)):
        ckpt_id = latest_ckpt_id - ckpt_idx
        is_failed = ckpt_idx == 0 and rng.random() < 0.1  # 10% chance latest failed
        trigger_ts = now_ms - (ckpt_idx * rng.randint(30_000, 300_000))
        ckpt_duration = rng.randint(500, 15_000)  # 500ms to 15s
        state_size = rng.randint(1_000_000, 500_000_000)  # 1MB to 500MB

        history.append(
            {
                "id": ckpt_id,
                "status": "FAILED" if is_failed else "COMPLETED",
                "is_savepoint": False,
                "trigger_timestamp": trigger_ts,
                "latest_ack_timestamp": trigger_ts + ckpt_duration,
                "end_to_end_duration": ckpt_duration,
                "state_size": state_size,
                "alignment_buffered": rng.randint(0, state_size // 10),
                "num_subtasks": rng.choice([4, 8, 12, 16]),
                "num_acknowledged_subtasks": rng.choice([4, 8, 12, 16]),
                "checkpoint_type": "CHECKPOINT",
            }
        )

    latest = history[0] if history else None

    return {
        "counts": {
            "restored": rng.randint(0, 3),
            "total": latest_ckpt_id,
            "in_progress": 1 if job["state"] == "RUNNING" and rng.random() < 0.3 else 0,
            "completed": num_completed,
            "failed": num_failed,
        },
        "summary": {
            "state_size": {
                "min": min(h["state_size"] for h in history) if history else 0,
                "max": max(h["state_size"] for h in history) if history else 0,
                "avg": (
                    sum(h["state_size"] for h in history) // len(history)
                    if history
                    else 0
                ),
            },
            "end_to_end_duration": {
                "min": min(h["end_to_end_duration"] for h in history) if history else 0,
                "max": max(h["end_to_end_duration"] for h in history) if history else 0,
                "avg": (
                    sum(h["end_to_end_duration"] for h in history) // len(history)
                    if history
                    else 0
                ),
            },
            "alignment_buffered": {
                "min": min(h["alignment_buffered"] for h in history) if history else 0,
                "max": max(h["alignment_buffered"] for h in history) if history else 0,
                "avg": (
                    sum(h["alignment_buffered"] for h in history) // len(history)
                    if history
                    else 0
                ),
            },
        },
        "latest": latest,
        "history": history,
    }
