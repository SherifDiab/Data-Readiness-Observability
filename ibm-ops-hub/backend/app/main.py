"""
IBM Ops Hub — FastAPI application entry point.
Configures CORS, lifespan events (Redis, DB, scheduler), and mounts all routers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cache import close_redis, init_redis
from app.database import init_db
from app.polling.scheduler import start_scheduler, stop_scheduler
from app.routers import apic, dashboard, datastage, event_processing, flink, spark, ws
from app.routers import settings_router
from app.settings_store import load_overrides_on_startup
from app.utils.http_client import close_http_client

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting IBM Ops Hub...")
    await init_redis()
    await load_overrides_on_startup()   # restore any runtime settings saved in Redis
    await init_db()
    await start_scheduler()
    logger.info("IBM Ops Hub started successfully")
    yield
    logger.info("Shutting down IBM Ops Hub...")
    await stop_scheduler()
    await close_http_client()
    await close_redis()
    logger.info("IBM Ops Hub shut down")


app = FastAPI(
    title="IBM Ops Hub",
    description="Unified monitoring dashboard for IBM platform components",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(spark.router, prefix="/api/spark", tags=["Spark"])
app.include_router(datastage.router, prefix="/api/datastage", tags=["DataStage"])
app.include_router(event_processing.router, prefix="/api/event-processing", tags=["Event Processing"])
app.include_router(flink.router, prefix="/api/flink", tags=["Flink"])
app.include_router(apic.router, prefix="/api/apic", tags=["API Connect"])
app.include_router(ws.router, tags=["WebSocket"])
app.include_router(settings_router.router, prefix="/api/settings", tags=["Settings"])


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "ibm-ops-hub"}
