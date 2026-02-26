"""
Mock DataStage API
==================
Simulates IBM DataStage flow listing and job-run endpoints.
- GET /data_intg/v3/data_intg_flows          -> list DataStage flows
- Reuses /v2/jobs (with asset_ref_type=data_intg_flow filter from mock_spark)
- GET /v2/jobs/{job_id}/runs extended with rows_read / rows_written
"""

import hashlib
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()

BASE_SEED = 77

DS_FLOW_NAMES = [
    "DS_Customer_Transform",
    "DS_Product_Inventory_Sync",
    "DS_Order_Fulfillment_ETL",
    "DS_Financial_Reconciliation",
    "DS_Employee_Onboarding_Load",
    "DS_Supplier_Data_Harmonize",
    "DS_CRM_Contact_Merge",
    "DS_Marketing_Lead_Scoring",
    "DS_Billing_Invoice_Transform",
    "DS_Warehouse_Stock_Levels",
    "DS_Sales_Pipeline_Aggregate",
    "DS_Customer_Address_Cleanse",
    "DS_Regulatory_Compliance_Load",
    "DS_Shipment_Tracking_Enrich",
    "DS_Web_Clickstream_Flatten",
    "DS_Loyalty_Program_Points_Calc",
    "DS_Returns_Refunds_Reconcile",
    "DS_Partner_Revenue_Share",
    "DS_Healthcare_Claims_Validate",
    "DS_IoT_Device_Telemetry_Parse",
    "DS_HR_Benefits_Enrollment",
    "DS_Vendor_Payment_Match",
    "DS_Customer_Segmentation_Build",
    "DS_Fraud_Alert_Staging",
    "DS_Data_Archive_Compress",
]

DS_FLOW_DESCRIPTIONS = [
    "Transforms and cleanses customer master records from CRM",
    "Synchronizes product inventory levels across warehouses",
    "ETL pipeline for order fulfillment data from multiple channels",
    "Reconciles financial transactions against GL entries",
    "Loads new employee data into HR and payroll systems",
    "Harmonizes supplier data from various procurement sources",
    "Merges and deduplicates CRM contact records",
    "Scores marketing leads based on engagement signals",
    "Transforms billing invoices into standardized format",
    "Aggregates warehouse stock levels for inventory reporting",
    "Aggregates sales pipeline data for forecasting",
    "Cleanses and standardizes customer address records",
    "Loads regulatory compliance data for audit reporting",
    "Enriches shipment tracking data with carrier details",
    "Flattens nested clickstream events into analytical tables",
    "Calculates loyalty program point balances and tiers",
    "Reconciles product returns with refund transactions",
    "Calculates partner revenue-sharing amounts monthly",
    "Validates healthcare claims against policy rules",
    "Parses raw IoT telemetry into structured time-series",
    "Processes HR benefits enrollment changes",
    "Matches vendor payments to purchase orders",
    "Builds customer segmentation based on RFM analysis",
    "Stages fraud alert signals for investigation workflow",
    "Compresses and archives aged data to cold storage",
]

RUN_STATES = ["Queued", "Starting", "Running", "Completed", "Failed", "Canceled"]


def _deterministic_uuid(seed_str: str) -> str:
    h = hashlib.sha256(seed_str.encode()).hexdigest()
    return f"{h[:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


# ---------------------------------------------------------------------------
# Data generators
# ---------------------------------------------------------------------------


def _generate_ds_flows():
    """Generate the list of DataStage integration flows."""
    rng = random.Random(BASE_SEED)
    flows = []
    for idx, name in enumerate(DS_FLOW_NAMES):
        flow_id = _deterministic_uuid(f"ds-flow-{idx}")
        flows.append(
            {
                "metadata": {
                    "asset_id": flow_id,
                    "name": name,
                    "description": DS_FLOW_DESCRIPTIONS[idx],
                    "asset_type": "data_intg_flow",
                    "origin_country": "us",
                    "created_at": (
                        datetime(2025, 1, 10, tzinfo=timezone.utc)
                        + timedelta(days=idx * 2, hours=rng.randint(0, 23))
                    ).isoformat(),
                    "owner_id": _deterministic_uuid(f"ds-owner-{idx % 4}"),
                },
                "entity": {
                    "data_intg_flow": {
                        "pipeline_type": rng.choice(
                            ["batch", "batch", "batch", "microbatch"]
                        ),
                        "locked": rng.choice([False, False, False, True]),
                        "nodes_count": rng.randint(3, 18),
                        "links_count": rng.randint(2, 17),
                        "source_connections": rng.randint(1, 4),
                        "target_connections": rng.randint(1, 3),
                    }
                },
                "href": f"/data_intg/v3/data_intg_flows/{flow_id}",
            }
        )
    return flows


def _generate_ds_jobs(project_id: Optional[str] = None):
    """Generate DataStage jobs that reference the DS flows."""
    rng = random.Random(BASE_SEED + 1)
    flows = _generate_ds_flows()
    jobs = []
    for idx, flow in enumerate(flows):
        asset_id = _deterministic_uuid(f"ds-job-{idx}")
        proj = project_id or _deterministic_uuid(f"ds-project-{idx % 2}")
        jobs.append(
            {
                "metadata": {
                    "asset_id": asset_id,
                    "name": flow["metadata"]["name"].replace("DS_", "Job_DS_"),
                    "description": f"Scheduled job for {flow['metadata']['name']}",
                    "created_at": flow["metadata"]["created_at"],
                },
                "entity": {
                    "job": {
                        "asset_ref": flow["metadata"]["asset_id"],
                        "asset_ref_type": "data_intg_flow",
                        "configuration": {
                            "env_type": "datastage",
                            "env_id": _deterministic_uuid(f"env-ds-{idx % 3}"),
                        },
                        "last_run_initiator": rng.choice(["scheduler", "user"]),
                        "last_run_time": (
                            datetime.now(timezone.utc) - timedelta(hours=rng.randint(1, 48))
                        ).isoformat(),
                        "schedule_info": {
                            "frequency": rng.choice(
                                ["hourly", "daily", "weekly"]
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
    now_seconds = int(time.time())
    cycle_period = 35 + (job_idx * 11) + (run_idx * 7)
    state_index = (now_seconds // cycle_period + job_idx + run_idx) % len(RUN_STATES)
    return RUN_STATES[state_index]


def _generate_ds_runs(job_id: str, job_idx: int):
    """Generate 1-5 mock DataStage runs with row counts."""
    rng = random.Random(f"{BASE_SEED}-ds-runs-{job_id}")
    num_runs = rng.randint(1, 5)
    runs = []
    base_time = datetime.now(timezone.utc) - timedelta(hours=num_runs * 4)

    for run_idx in range(num_runs):
        run_id = _deterministic_uuid(f"ds-run-{job_id}-{run_idx}")
        state = _time_based_state(job_idx, run_idx)

        created_at = base_time + timedelta(hours=run_idx * 4, minutes=rng.randint(0, 20))
        started_at = None
        finished_at = None
        duration = None

        if state in ("Starting", "Running", "Completed", "Failed", "Canceled"):
            started_at = created_at + timedelta(seconds=rng.randint(3, 60))

        if state in ("Completed", "Failed", "Canceled"):
            run_duration = rng.randint(45, 5400)
            finished_at = (started_at + timedelta(seconds=run_duration)) if started_at else None
            duration = run_duration

        # Row counts - only for runs that have started processing
        rows_read = 0
        rows_written = 0
        if state in ("Running", "Completed", "Failed", "Canceled"):
            base_rows = rng.randint(10_000, 5_000_000)
            # Running jobs have partial row counts that increase over time
            if state == "Running":
                elapsed_fraction = (int(time.time()) % 300) / 300.0
                rows_read = int(base_rows * elapsed_fraction)
                rows_written = int(rows_read * rng.uniform(0.85, 0.99))
            elif state == "Completed":
                rows_read = base_rows
                rows_written = int(base_rows * rng.uniform(0.95, 1.0))
            elif state == "Failed":
                rows_read = int(base_rows * rng.uniform(0.1, 0.7))
                rows_written = int(rows_read * rng.uniform(0.3, 0.8))
            elif state == "Canceled":
                rows_read = int(base_rows * rng.uniform(0.05, 0.5))
                rows_written = int(rows_read * rng.uniform(0.5, 0.9))

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
                        "env_type": "datastage",
                    },
                    "data_flow_stats": {
                        "rows_read": rows_read,
                        "rows_written": rows_written,
                        "rows_rejected": max(0, rows_read - rows_written),
                        "bytes_read": rows_read * rng.randint(200, 1200),
                        "bytes_written": rows_written * rng.randint(180, 1000),
                    },
                }
            },
            "href": f"/v2/jobs/{job_id}/runs/{run_id}",
        }

        if state == "Failed":
            run_entry["entity"]["job_run"]["error"] = {
                "code": rng.choice(
                    [
                        "DS_CONNECTOR_ERROR",
                        "DS_TRANSFORM_ERROR",
                        "DS_SCHEMA_MISMATCH",
                        "DS_RESOURCE_LIMIT",
                    ]
                ),
                "message": rng.choice(
                    [
                        "Connection to source database timed out after 300s",
                        "Column type mismatch: expected INTEGER, got VARCHAR",
                        "Schema drift detected - 3 new columns in source",
                        "DataStage PX engine exceeded memory allocation",
                    ]
                ),
            }

        runs.append(run_entry)

    return runs


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/data_intg/v3/data_intg_flows")
async def list_datastage_flows(
    project_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List DataStage integration flows."""
    all_flows = _generate_ds_flows()
    total = len(all_flows)
    page = all_flows[offset : offset + limit]

    return {
        "total_results": total,
        "limit": limit,
        "offset": offset,
        "results": page,
    }


@router.get("/data_intg/v3/data_intg_flows/{flow_id}")
async def get_datastage_flow(flow_id: str):
    """Get a single DataStage flow by ID."""
    flows = _generate_ds_flows()
    for f in flows:
        if f["metadata"]["asset_id"] == flow_id:
            return f
    return {"error": {"code": "not_found", "message": f"Flow {flow_id} not found"}}, 404


@router.get("/data_intg/v3/ds_jobs")
async def list_datastage_jobs(
    project_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """
    List DataStage jobs. These are jobs whose asset_ref_type is 'data_intg_flow'.
    This is a convenience endpoint; the /v2/jobs endpoint with
    asset_ref_type=data_intg_flow also returns these.
    """
    all_jobs = _generate_ds_jobs(project_id)
    total = len(all_jobs)
    page = all_jobs[offset : offset + limit]

    return {
        "total_results": total,
        "limit": limit,
        "offset": offset,
        "results": page,
    }


@router.get("/data_intg/v3/ds_jobs/{job_id}/runs")
async def list_datastage_job_runs(
    job_id: str,
    project_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List runs for a DataStage job with row-level stats."""
    all_jobs = _generate_ds_jobs(project_id)
    job_idx = 0
    for i, j in enumerate(all_jobs):
        if j["metadata"]["asset_id"] == job_id:
            job_idx = i
            break

    runs = _generate_ds_runs(job_id, job_idx)
    total = len(runs)
    page = runs[offset : offset + limit]

    return {
        "total_results": total,
        "limit": limit,
        "offset": offset,
        "results": page,
    }
