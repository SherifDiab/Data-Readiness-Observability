"""
APScheduler setup for background polling of all IBM services.

On each poll cycle:
1. Call service.poll() to fetch latest job data
2. Cache results in Redis
3. Persist new/changed statuses to PostgreSQL
4. Broadcast updates via WebSocket to connected clients
5. Check for failures and trigger alerts if enabled

Error isolation: each service failure is caught independently,
so one service down doesn't affect others.
"""

import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.cache import get_redis
from app.config import settings
from app.services.auth_service import AuthService
from app.services.spark_service import SparkService
from app.services.datastage_service import DataStageService
from app.services.flink_service import FlinkService
from app.services.event_processing_service import EventProcessingService
from app.services.apic_service import ApicService
from app.utils.http_client import get_http_client
from app.websocket_manager import manager

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None

# Service singletons initialized at startup
_spark_service: SparkService | None = None
_datastage_service: DataStageService | None = None
_flink_service: FlinkService | None = None
_event_processing_service: EventProcessingService | None = None
_apic_service: ApicService | None = None


def get_spark_service() -> SparkService | None:
    return _spark_service

def get_datastage_service() -> DataStageService | None:
    return _datastage_service

def get_flink_service() -> FlinkService | None:
    return _flink_service

def get_event_processing_service() -> EventProcessingService | None:
    return _event_processing_service

def get_apic_service() -> ApicService | None:
    return _apic_service


async def _poll_spark():
    if not _spark_service:
        return
    try:
        jobs = await _spark_service.poll()
        data = [j.model_dump(mode="json") for j in jobs]
        await manager.broadcast("spark", data)
        logger.info("Spark poll: %d jobs", len(jobs))
    except Exception as e:
        logger.error("Spark poll error: %s", e)


async def _poll_datastage():
    if not _datastage_service:
        return
    try:
        jobs = await _datastage_service.poll()
        data = [j.model_dump(mode="json") for j in jobs]
        await manager.broadcast("datastage", data)
        logger.info("DataStage poll: %d jobs", len(jobs))
    except Exception as e:
        logger.error("DataStage poll error: %s", e)


async def _poll_flink():
    if not _flink_service:
        return
    try:
        jobs = await _flink_service.poll()
        data = [j.model_dump(mode="json") for j in jobs]
        await manager.broadcast("flink", data)
        logger.info("Flink poll: %d jobs", len(jobs))
    except Exception as e:
        logger.error("Flink poll error: %s", e)


async def _poll_event_processing():
    if not _event_processing_service:
        return
    try:
        flows = await _event_processing_service.poll()
        data = [f.model_dump(mode="json") for f in flows]
        await manager.broadcast("event_processing", data)
        logger.info("EventProcessing poll: %d flows", len(flows))
    except Exception as e:
        logger.error("EventProcessing poll error: %s", e)


async def _poll_apic():
    if not _apic_service:
        return
    try:
        await _apic_service.poll_analytics()
        await manager.broadcast("apic", {"refreshed": True})
        logger.info("APIC poll complete")
    except Exception as e:
        logger.error("APIC poll error: %s", e)


async def _heartbeat():
    await manager.send_heartbeat()


async def start_scheduler():
    global _scheduler, _spark_service, _datastage_service, _flink_service, _event_processing_service, _apic_service

    redis = get_redis()
    http_client = await get_http_client()
    auth = AuthService(settings, redis, http_client)

    _spark_service = SparkService(auth, settings, redis, http_client)
    _datastage_service = DataStageService(auth, settings, redis, http_client)
    _flink_service = FlinkService(settings, redis, http_client)
    _event_processing_service = EventProcessingService(settings, redis, http_client)
    _apic_service = ApicService(settings, redis, http_client, auth)

    _scheduler = AsyncIOScheduler(timezone="UTC")

    _scheduler.add_job(_poll_spark, IntervalTrigger(seconds=settings.SPARK_POLL_INTERVAL), id="spark", replace_existing=True)
    _scheduler.add_job(_poll_datastage, IntervalTrigger(seconds=settings.DATASTAGE_POLL_INTERVAL), id="datastage", replace_existing=True)
    _scheduler.add_job(_poll_flink, IntervalTrigger(seconds=settings.FLINK_POLL_INTERVAL), id="flink", replace_existing=True)
    _scheduler.add_job(_poll_event_processing, IntervalTrigger(seconds=settings.EVENT_PROCESSING_POLL_INTERVAL), id="event_processing", replace_existing=True)
    _scheduler.add_job(_poll_apic, IntervalTrigger(seconds=settings.APIC_POLL_INTERVAL), id="apic", replace_existing=True)
    _scheduler.add_job(_heartbeat, IntervalTrigger(seconds=30), id="heartbeat", replace_existing=True)

    _scheduler.start()
    logger.info("Scheduler started with %d jobs", len(_scheduler.get_jobs()))

    # Trigger initial polls immediately
    for poll_fn in [_poll_spark, _poll_datastage, _poll_flink, _poll_event_processing, _poll_apic]:
        try:
            await poll_fn()
        except Exception as e:
            logger.warning("Initial poll failed (will retry): %s", e)


async def stop_scheduler():
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Scheduler stopped")


async def trigger_poll(component: str):
    """Force immediate re-poll of a specific component."""
    poll_map = {
        "spark": _poll_spark,
        "datastage": _poll_datastage,
        "flink": _poll_flink,
        "event_processing": _poll_event_processing,
        "apic": _poll_apic,
    }
    fn = poll_map.get(component)
    if fn:
        await fn()
