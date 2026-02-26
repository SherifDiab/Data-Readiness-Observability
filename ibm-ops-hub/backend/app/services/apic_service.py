"""
API Connect Service — polls IBM APIC Analytics REST API for call logs and metrics.

Authentication:
  POST {APIC_MGMT_URL}/api/token
  Body: {"username": ..., "password": ..., "realm": "provider/default-idp-2", "grant_type": "password"}
  → {"access_token": "...", "expires_in": 28800}

Events endpoint:
  GET {APIC_ANALYTICS_URL}/analytics/{org}/{catalog}/events
  Query: timeframe=last1hour, limit=500
  Headers: Authorization: Bearer <token>

Each event has: datetime, api_name, api_version, request_method, uri_path,
               status_code, time_to_serve_request, developer_org_name, app_name.

Cache keys:
  "apic:logs"    → recent ApiCallLog list
  "apic:summary" → ApicSummary computed from raw events
"""

import logging
import statistics
from collections import defaultdict
from datetime import datetime, timezone

import httpx

import redis.asyncio as aioredis

from app.config import Settings
from app.schemas import (
    ApiCallLog,
    ApicSummary,
    ComponentHealth,
    ComponentType,
    JobStatus,
    NormalizedJob,
)
from app.services.base_service import BaseService
from app.services.auth_service import AuthService
from app.utils.normalize import compute_health

logger = logging.getLogger(__name__)

LOGS_CACHE_KEY = "apic:logs"
SUMMARY_CACHE_KEY = "apic:summary"


class ApicService(BaseService):
    """Polls IBM API Connect Analytics API for call logs and computes summary metrics."""

    def __init__(self, settings: Settings, redis: aioredis.Redis, http_client: httpx.AsyncClient, auth: AuthService):
        super().__init__(settings, redis, http_client)
        self.auth = auth

    async def poll(self) -> list[NormalizedJob]:
        """APIC doesn't have 'jobs'; poll_analytics() is the main data collection."""
        await self.poll_analytics()
        return []

    async def poll_analytics(self, timeframe: str = "last1hour") -> tuple[list[ApiCallLog], ApicSummary]:
        """Fetch analytics events and compute summary metrics."""
        try:
            if self.settings.MOCK_MODE:
                base_url = self.settings.MOCK_SERVER_URL
                token = "mock-token"
            else:
                base_url = self.settings.APIC_ANALYTICS_URL
                token = await self.auth.get_apic_token()

            url = f"{base_url}/analytics/{self.settings.APIC_ORG}/{self.settings.APIC_CATALOG}/events"
            params = {"timeframe": timeframe, "limit": 500}
            headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

            self.logger.info("APIC: GET %s", url)
            resp = await self.client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            data = resp.json()

            events = data.get("events", data) if isinstance(data, dict) else data
            if not isinstance(events, list):
                events = []

            logs = [self._parse_event(e) for e in events if e]
            summary = self._compute_summary(logs, timeframe)

            await self.cache_results(
                LOGS_CACHE_KEY,
                [l.model_dump(mode="json") for l in logs[:500]],
                ttl=120,
            )
            await self.cache_results(
                SUMMARY_CACHE_KEY,
                [summary.model_dump(mode="json")],
                ttl=120,
            )
            return logs, summary

        except Exception as e:
            self.logger.error("APIC poll failed: %s", e)
            return [], self._empty_summary(timeframe)

    def _parse_event(self, event: dict) -> ApiCallLog:
        timestamp_str = event.get("datetime") or event.get("timestamp") or datetime.now(timezone.utc).isoformat()
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            ts = datetime.now(timezone.utc)

        return ApiCallLog(
            timestamp=ts,
            api_name=event.get("api_name") or event.get("api", "Unknown"),
            path=event.get("uri_path") or event.get("path", "/"),
            method=event.get("request_method") or event.get("method", "GET"),
            status_code=int(event.get("status_code", 200)),
            latency_ms=float(event.get("time_to_serve_request") or event.get("latency_ms", 0)),
            client_ip=event.get("client_ip"),
            consumer_org=event.get("developer_org_name") or event.get("consumer_org"),
        )

    def _compute_summary(self, logs: list[ApiCallLog], timeframe: str) -> ApicSummary:
        if not logs:
            return self._empty_summary(timeframe)

        latencies = [l.latency_ms for l in logs]
        errors = [l for l in logs if l.status_code >= 400]
        successes = [l for l in logs if l.status_code < 400]

        sorted_latencies = sorted(latencies)
        p95_idx = int(len(sorted_latencies) * 0.95)
        p95 = sorted_latencies[p95_idx] if sorted_latencies else 0.0

        # Top errors grouped by (status_code, api_name)
        error_counts: dict[tuple, int] = defaultdict(int)
        for l in errors:
            error_counts[(l.status_code, l.api_name)] += 1
        top_errors = [
            {"status_code": k[0], "api": k[1], "count": v}
            for k, v in sorted(error_counts.items(), key=lambda x: -x[1])[:10]
        ]

        # Calls grouped by minute
        minute_counts: dict[str, int] = defaultdict(int)
        for l in logs:
            minute_key = l.timestamp.strftime("%Y-%m-%dT%H:%M")
            minute_counts[minute_key] += 1
        calls_by_minute = [
            {"minute": k, "count": v}
            for k, v in sorted(minute_counts.items())
        ]

        return ApicSummary(
            total_calls=len(logs),
            success_count=len(successes),
            error_count=len(errors),
            avg_latency_ms=statistics.mean(latencies) if latencies else 0.0,
            p95_latency_ms=p95,
            error_rate_percent=(len(errors) / len(logs) * 100) if logs else 0.0,
            top_errors=top_errors,
            calls_by_minute=calls_by_minute,
            timeframe=timeframe,
        )

    def _empty_summary(self, timeframe: str) -> ApicSummary:
        return ApicSummary(
            total_calls=0, success_count=0, error_count=0,
            avg_latency_ms=0.0, p95_latency_ms=0.0, error_rate_percent=0.0,
            top_errors=[], calls_by_minute=[], timeframe=timeframe,
        )

    async def get_logs_cached(self, timeframe: str = "last1hour") -> tuple[list[ApiCallLog], ApicSummary]:
        logs_raw = await self.get_cached(LOGS_CACHE_KEY)
        summary_raw = await self.get_cached(SUMMARY_CACHE_KEY)

        if logs_raw and summary_raw:
            logs = [ApiCallLog(**l) for l in logs_raw]
            summary = ApicSummary(**summary_raw[0]) if isinstance(summary_raw, list) else ApicSummary(**summary_raw)
            return logs, summary

        return await self.poll_analytics(timeframe)

    async def get_health(self) -> ComponentHealth:
        summary_raw = await self.get_cached(SUMMARY_CACHE_KEY)
        if not summary_raw:
            return compute_health(ComponentType.APIC, [], is_reachable=False, error_message="No APIC data cached")

        s = summary_raw[0] if isinstance(summary_raw, list) else summary_raw
        error_rate = s.get("error_rate_percent", 0)

        # Create synthetic health from APIC summary
        from app.schemas import ComponentHealth
        return ComponentHealth(
            component=ComponentType.APIC,
            total_jobs=s.get("total_calls", 0),
            running=s.get("success_count", 0),
            completed=0,
            failed=s.get("error_count", 0),
            warning=0,
            other=0,
            last_polled_at=datetime.now(timezone.utc),
            is_reachable=True,
            error_message=f"Error rate: {error_rate:.1f}%" if error_rate > 10 else None,
        )
