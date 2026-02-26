"""
IBM Ops Hub - Mock Server
=========================
Central FastAPI application that mounts all mock service routers.
Simulates CPD Spark, DataStage, Flink, Kubernetes, and API Connect APIs.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.mock_spark import router as spark_router
from app.mock_datastage import router as datastage_router
from app.mock_flink import router as flink_router
from app.mock_k8s import router as k8s_router
from app.mock_apic import router as apic_router

app = FastAPI(
    title="IBM Ops Hub Mock Server",
    description="Mock APIs for CPD Spark, DataStage, Flink, Kubernetes, and API Connect",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS - allow all origins for local development
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Mount routers
# ---------------------------------------------------------------------------
app.include_router(spark_router, tags=["CPD Spark"])
app.include_router(datastage_router, tags=["DataStage"])
app.include_router(flink_router, tags=["Flink"])
app.include_router(k8s_router, tags=["Kubernetes / Flink Operator"])
app.include_router(apic_router, tags=["API Connect"])


@app.get("/", tags=["Health"])
async def root():
    return {
        "service": "IBM Ops Hub Mock Server",
        "status": "healthy",
        "endpoints": {
            "spark": "/icp4d-api/v1/authorize, /v2/jobs, /v2/jobs/{job_id}/runs",
            "datastage": "/data_intg/v3/data_intg_flows, /v2/jobs (asset_ref_type=data_intg_flow)",
            "flink": "/overview, /jobs/overview, /jobs/{jid}/exceptions, /jobs/{jid}/checkpoints",
            "kubernetes": "/apis/flink.apache.org/v1beta1/namespaces/{ns}/flinkdeployments",
            "apic": "/api/token, /analytics/{org}/{catalog}/events",
        },
    }


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok"}
