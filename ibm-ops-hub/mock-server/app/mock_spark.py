"""
Mock CPD Spark API
==================
Simulates IBM Cloud Pak for Data Spark job management endpoints.
- POST /icp4d-api/v1/authorize       -> CPD token
- GET  /v2/jobs                       -> list Spark jobs
- GET  /v2/jobs/{job_id}/runs         -> runs for a given job
"""

import hashlib
import math
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()

# ---------------------------------------------------------------------------
# Seed-based helpers
# ---------------------------------------------------------------------------
BASE_SEED = 42

SPARK_JOB_NAMES = [
    "ETL_Customer_Data_Load",
    "ML_Model_Training_Pipeline",
    "ETL_Product_Catalog_Refresh",
    "Batch_Revenue_Aggregation",
    "Customer_Churn_Scoring",
    "ETL_Transaction_History_Ingest",
    "Feature_Engineering_Pipeline",
    "Data_Quality_Validation_Suite",
    "ETL_Clickstream_SessionBuilder",
    "Recommendation_Engine_Retrain",
    "ETL_Inventory_Snapshot",
    "Fraud_Risk_Score_Batch",
    "Customer_360_Profile_Build",
    "ETL_Marketing_Campaign_Metrics",
    "Sentiment_Analysis_Batch",
    "ETL_Supply_Chain_Data_Merge",
    "A_B_Test_Results_Aggregator",
    "ETL_Financial_Ledger_Reconcile",
    "Graph_Analytics_Social_Network",
    "ETL_IoT_Sensor_Data_Compress",
    "Price_Optimization_Model_Run",
    "ETL_HR_Payroll_Transform",
    "NLP_Document_Classification",
    "ETL_Geospatial_Data_Enrichment",
    "Data_Lineage_Metadata_Scan",
]

SPARK_JOB_DESCRIPTIONS = [
    "Loads and transforms customer master data from multiple sources",
    "Trains ML model on latest feature set and publishes metrics",
    "Refreshes the product catalog from upstream ERP system",
    "Aggregates daily revenue numbers across all business units",
    "Computes churn probability scores for the customer base",
    "Ingests 90-day transaction history into the data lake",
    "Builds feature vectors for the recommendation engine",
    "Runs data quality checks against golden-record standards",
    "Sessionizes raw clickstream events from the web platform",
    "Retrains collaborative-filtering recommendation model",
    "Captures nightly inventory snapshot for warehouse analytics",
    "Calculates batch fraud risk scores for pending transactions",
    "Merges data from CRM, transactions, and support tickets",
    "Computes marketing campaign performance KPIs",
    "Runs sentiment analysis over latest customer feedback",
    "Merges and reconciles supply-chain data across regions",
    "Aggregates A/B test variant results for statistical analysis",
    "Reconciles financial ledger entries against source systems",
    "Runs PageRank and community detection on social graph",
    "Compresses and partitions raw IoT sensor readings",
    "Runs price elasticity optimization model",
    "Transforms and validates HR payroll data monthly",
    "Classifies documents using pre-trained NLP model",
    "Enriches address data with lat/long and geo-features",
    "Scans metadata catalog for lineage relationships",
]

RUN_STATES = ["Queued", "Starting", "Running", "Completed", "Failed", "Canceled"]


def _deterministic_uuid(seed_str: str) -> str:
    """Generate a deterministic UUID-like string from a seed."""
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


def _generate_spark_jobs(project_id: Optional[str] = None):
    """Generate the list of mock Spark jobs."""
    rng = random.Random(BASE_SEED)
    jobs = []
    for idx, name in enumerate(SPARK_JOB_NAMES):
        asset_id = _deterministic_uuid(f"spark-job-{idx}")
        proj = project_id or _deterministic_uuid(f"project-{idx % 3}")
        jobs.append(
            {
                "metadata": {
                    "asset_id": asset_id,
                    "name": name,
                    "description": SPARK_JOB_DESCRIPTIONS[idx],
                    "owner_id": _deterministic_uuid(f"owner-{idx % 5}"),
                    "created_at": (
                        datetime(2025, 1, 1, tzinfo=timezone.utc)
                        + timedelta(days=idx * 3, hours=rng.randint(0, 23))
                    ).isoformat(),
                },
                "entity": {
                    "job": {
                        "asset_ref": _deterministic_uuid(f"spark-asset-ref-{idx}"),
                        "asset_ref_type": "notebook" if idx % 3 != 0 else "script",
                        "configuration": {
                            "env_type": "spark",
                            "env_id": _deterministic_uuid(f"env-spark-{idx % 4}"),
                        },
                        "last_run_initiator": "scheduler" if idx % 2 == 0 else "user",
                        "last_run_time": (
                            datetime.now(timezone.utc) - timedelta(hours=rng.randint(1, 72))
                        ).isoformat(),
                        "schedule_info": {
                            "frequency": rng.choice(
                                ["hourly", "daily", "weekly", "monthly"]
                            ),
                            "enabled": rng.choice([True, True, True, False]),
                        },
                    }
                },
                "href": f"/v2/jobs/{asset_id}?project_id={proj}",
            }
        )
    return jobs


def _time_based_state(job_idx: int, run_idx: int) -> str:
    """Determine run state based on current time so states cycle on each poll."""
    now_seconds = int(time.time())
    # Each job/run combo cycles through states on a different cadence
    cycle_period = 30 + (job_idx * 7) + (run_idx * 13)  # seconds per state change
    state_index = (now_seconds // cycle_period + job_idx + run_idx) % len(RUN_STATES)
    return RUN_STATES[state_index]


def _generate_runs(job_id: str, job_idx: int):
    """Generate 1-5 mock runs for a given job."""
    rng = random.Random(f"{BASE_SEED}-runs-{job_id}")
    num_runs = rng.randint(1, 5)
    runs = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=num_runs * 6)

    for run_idx in range(num_runs):
        run_id = _deterministic_uuid(f"run-{job_id}-{run_idx}")
        state = _time_based_state(job_idx, run_idx)

        created_at = base_time + timedelta(hours=run_idx * 6, minutes=rng.randint(0, 30))
        started_at = None
        finished_at = None
        duration = None

        if state in ("Starting", "Running", "Completed", "Failed", "Canceled"):
            started_at = created_at + timedelta(seconds=rng.randint(5, 120))

        if state in ("Completed", "Failed", "Canceled"):
            run_duration = rng.randint(30, 7200)  # 30s to 2h
            finished_at = started_at + timedelta(seconds=run_duration) if started_at else None
            duration = run_duration

        run_entry = {
            "metadata": {
                "asset_id": run_id,
                "created_at": created_at.isoformat(),
            },
            "entity": {
                "job_run": {
                    "state": state,
                    "run_id": run_id,
                    "job_id": job_id,
                    "started_at": started_at.isoformat() if started_at else None,
                    "finished_at": finished_at.isoformat() if finished_at else None,
                    "duration": duration,
                    "configuration": {
                        "env_type": "spark",
                    },
                    "compute": {
                        "instance_type": rng.choice(
                            ["spark-2x4", "spark-4x8", "spark-8x16"]
                        ),
                        "num_executors": rng.choice([2, 4, 8, 16]),
                    },
                }
            },
            "href": f"/v2/jobs/{job_id}/runs/{run_id}",
        }

        # Add error info for failed runs
        if state == "Failed":
            run_entry["entity"]["job_run"]["error"] = {
                "code": rng.choice(
                    ["SPARK_OOM", "TASK_FAILED", "DRIVER_ERROR", "TIMEOUT"]
                ),
                "message": rng.choice(
                    [
                        "Java heap space - OutOfMemoryError in executor",
                        "Task failed after 4 retries due to FetchFailedException",
                        "Driver process terminated unexpectedly with exit code 137",
                        "Job exceeded maximum runtime limit of 7200 seconds",
                    ]
                ),
            }

        runs.append(run_entry)

    return runs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/icp4d-api/v1/authorize")
async def authorize():
    """Simulate CPD token generation."""
    token_suffix = hashlib.sha256(
        f"cpd-{int(time.time()) // 300}".encode()
    ).hexdigest()[:24]
    return {"token": f"mock-cpd-token-{token_suffix}"}


@router.get("/v2/jobs")
async def list_jobs(
    project_id: Optional[str] = Query(None),
    asset_ref_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List Spark jobs. Supports optional project_id and asset_ref_type filters.
    The asset_ref_type filter is also used by the DataStage mock.
    """
    all_jobs = _generate_spark_jobs(project_id)

    # Filter by asset_ref_type if provided (used by DataStage router)
    if asset_ref_type:
        all_jobs = [
            j
            for j in all_jobs
            if j["entity"]["job"]["asset_ref_type"] == asset_ref_type
        ]

    total = len(all_jobs)
    page = all_jobs[offset : offset + limit]

    return {
        "total_results": total,
        "limit": limit,
        "offset": offset,
        "results": page,
    }


@router.get("/v2/jobs/{job_id}/runs")
async def list_job_runs(
    job_id: str,
    project_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List runs for a specific Spark job. States cycle over time."""
    # Determine job index from the list for consistent state cycling
    all_jobs = _generate_spark_jobs(project_id)
    job_idx = 0
    for i, j in enumerate(all_jobs):
        if j["metadata"]["asset_id"] == job_id:
            job_idx = i
            break

    runs = _generate_runs(job_id, job_idx)
    total = len(runs)
    page = runs[offset : offset + limit]

    return {
        "total_results": total,
        "limit": limit,
        "offset": offset,
        "results": page,
    }
