"""
Tests for EventProcessingService.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import ComponentType, JobStatus
from app.services.event_processing_service import EventProcessingService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def ep_service(test_settings, mock_redis, mock_http_client):
    return EventProcessingService(test_settings, mock_redis, mock_http_client)


@pytest.fixture
def flinkdeployments_response():
    with open(FIXTURES / "flinkdeployments.json") as f:
        return json.load(f)


def test_state_mapping(ep_service):
    from app.services.event_processing_service import FLINK_STATE_MAP
    assert FLINK_STATE_MAP["RUNNING"] == JobStatus.RUNNING
    assert FLINK_STATE_MAP["FINISHED"] == JobStatus.COMPLETED
    assert FLINK_STATE_MAP["FAILED"] == JobStatus.FAILED
    assert FLINK_STATE_MAP["CANCELED"] == JobStatus.CANCELED
    assert FLINK_STATE_MAP["SUSPENDED"] == JobStatus.SUSPENDED
    assert FLINK_STATE_MAP["RECONCILING"] == JobStatus.RESTARTING


@pytest.mark.asyncio
async def test_poll_mock(ep_service, flinkdeployments_response):
    resp = MagicMock(spec=httpx.Response)
    resp.raise_for_status = MagicMock()
    resp.json.return_value = flinkdeployments_response
    ep_service.client.get = AsyncMock(return_value=resp)
    ep_service.redis.set = AsyncMock()

    flows = await ep_service._poll_mock()
    assert len(flows) == 1
    assert flows[0].job_name == "ep-customer-events-processor"
    assert flows[0].status == JobStatus.RUNNING
    assert flows[0].component == ComponentType.EVENT_PROCESSING
    assert flows[0].details["jm_deployment_status"] == "READY"
