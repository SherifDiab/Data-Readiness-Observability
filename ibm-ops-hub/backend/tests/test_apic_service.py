"""
Tests for ApicService using fixture data.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import ApiCallLog, ApicSummary
from app.services.apic_service import ApicService
from app.services.auth_service import AuthService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def auth_service(test_settings, mock_redis, mock_http_client):
    auth = MagicMock(spec=AuthService)
    auth.get_apic_token = AsyncMock(return_value="mock-token")
    return auth


@pytest.fixture
def apic_service(test_settings, mock_redis, mock_http_client, auth_service):
    return ApicService(test_settings, mock_redis, mock_http_client, auth_service)


@pytest.fixture
def apic_events_response():
    with open(FIXTURES / "apic_events.json") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_poll_analytics_parses_events(apic_service, apic_events_response):
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json.return_value = apic_events_response
    apic_service.client.get = AsyncMock(return_value=resp)
    apic_service.redis.set = AsyncMock()

    logs, summary = await apic_service.poll_analytics()

    assert len(logs) == 2
    assert summary.total_calls == 2
    assert summary.error_count == 1  # one 500 error
    assert summary.success_count == 1
    assert summary.error_rate_percent == 50.0


def test_compute_summary_empty(apic_service):
    summary = apic_service._compute_summary([], "last1hour")
    assert summary.total_calls == 0
    assert summary.error_rate_percent == 0.0
