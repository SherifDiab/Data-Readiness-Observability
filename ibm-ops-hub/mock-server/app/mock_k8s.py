"""
Mock Kubernetes API — simulates FlinkDeployment CRDs for Event Processing.
"""

import random
import time
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Path

router = APIRouter()

FLOW_NAMES = [
    "ep-customer-events-processor",
    "ep-order-stream-enricher",
    "ep-inventory-change-detector",
    "ep-fraud-realtime-scorer",
    "ep-payment-transaction-aggregator",
    "ep-clickstream-session-joiner",
    "ep-product-view-counter",
    "ep-user-activity-tracker",
    "ep-shipment-status-monitor",
    "ep-loyalty-points-calculator",
    "ep-api-latency-analyzer",
    "ep-log-anomaly-detector",
    "ep-market-data-normalizer",
    "ep-iot-sensor-aggregator",
    "ep-social-feed-filter",
]

JM_STATUSES = ["READY", "READY", "READY", "DEPLOYING", "ERROR", "MISSING"]
JOB_STATES = ["RUNNING", "RUNNING", "RUNNING", "RUNNING", "FINISHED", "FAILED", "CANCELED", "SUSPENDED", "RECONCILING"]
RECON_STATES = ["DEPLOYED", "DEPLOYED", "DEPLOYED", "UPGRADING", "ROLLING_BACK"]


def _make_flow(name: str, seed: int) -> dict:
    rng = random.Random(seed + int(time.time() // 60))
    state = rng.choice(JOB_STATES)
    jm_status = "READY" if state == "RUNNING" else rng.choice(JM_STATUSES)
    start_dt = datetime.now(timezone.utc) - timedelta(hours=rng.randint(1, 72))

    savepoint_ts = None
    if state in ("RUNNING", "FINISHED"):
        savepoint_ts = int((start_dt + timedelta(minutes=rng.randint(5, 60))).timestamp() * 1000)

    return {
        "apiVersion": "flink.apache.org/v1beta1",
        "kind": "FlinkDeployment",
        "metadata": {
            "name": name,
            "uid": str(uuid.uuid5(uuid.NAMESPACE_DNS, name)),
            "namespace": "event-automation",
            "creationTimestamp": start_dt.isoformat(),
        },
        "spec": {
            "image": "icr.io/cpopen/ibm-eventautomation-flink:1.17.1",
            "job": {
                "state": "running" if state not in ("SUSPENDED",) else "suspended",
                "parallelism": rng.choice([1, 2, 4, 8]),
            },
        },
        "status": {
            "jobStatus": {
                "state": state,
                "startTime": start_dt.isoformat(),
                "savepointInfo": {
                    "lastPeriodicSavepointTimestamp": savepoint_ts,
                } if savepoint_ts else {},
            },
            "jobManagerDeploymentStatus": jm_status,
            "reconciliationStatus": {
                "state": rng.choice(RECON_STATES),
                "lastReconciledSpec": None,
            },
        },
    }


@router.get("/apis/{group}/{version}/namespaces/{namespace}/flinkdeployments")
async def list_flinkdeployments(
    group: str = Path(...),
    version: str = Path(...),
    namespace: str = Path(...),
):
    items = [_make_flow(name, i) for i, name in enumerate(FLOW_NAMES)]
    return {"apiVersion": f"{group}/{version}", "kind": "FlinkDeploymentList", "items": items}
