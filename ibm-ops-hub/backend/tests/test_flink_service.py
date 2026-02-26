"""
Tests for FlinkService using fixture data.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import ComponentType, JobStatus, NormalizedJob
from app.services.flink_service import FlinkService

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def flink_service(test_settings, mock_redis, mock_http_client):
    return FlinkService(test_settings, mock_redis, mock_http_client)


@pytest.fixture
def flink_overview_response():
    with open(FIXTURES / "flink_overview.json") as f:
        return json.load(f)


def test_flink_state_mapping(flink_service):
    assert flink_service._map_state("RUNNING") == JobStatus.RUNNING
    assert flink_service._map_state("FINISHED") == JobStatus.COMPLETED
    assert flink_service._map_state("FAILED") == JobStatus.FAILED
    assert flink_service._map_state("FAILING") == JobStatus.FAILED
    assert flink_service._map_state("CANCELED") == JobStatus.CANCELED
    assert flink_service._map_state("CANCELLING") == JobStatus.CANCELED
    assert flink_service._map_state("CREATED") == JobStatus.QUEUED
    assert flink_service._map_state("RESTARTING") == JobStatus.RESTARTING
    assert flink_service._map_state("SUSPENDED") == JobStatus.SUSPENDED
    assert flink_service._map_state("RECONCILING") == JobStatus.RESTARTING
    assert flink_service._map_state("UNKNOWN_XYZ") == JobStatus.UNKNOWN


@pytest.mark.asyncio
async def test_poll_parses_jobs(flink_service, flink_overview_response):
    jobs_response = {
        "jobs": [
            {
                "jid": "abc123",
                "name": "TestFlinkJob",
                "state": "RUNNING",
                "start-time": 1740477600000,
                "end-time": -1,
                "duration": 60000,
                "last-modification": 1740477660000,
                "tasks": {"total": 4, "running": 4, "finished": 0, "failed": 0,
                          "created": 0, "scheduled": 0, "deploying": 0,
                          "canceling": 0, "canceled": 0, "reconciling": 0},
            }
        ]
    }

    def mock_get(url, **kwargs):
        resp = MagicMock(spec=httpx.Response)
        resp.raise_for_status = MagicMock()
        if "jobs/overview" in url:
            resp.json.return_value = jobs_response
        elif "/overview" in url:
            resp.json.return_value = flink_overview_response
        else:
            resp.json.return_value = {}
        return resp

    flink_service.client.get = AsyncMock(side_effect=mock_get)

    jobs = await flink_service.poll()
    assert len(jobs) == 1
    assert jobs[0].job_id == "abc123"
    assert jobs[0].job_name == "TestFlinkJob"
    assert jobs[0].status == JobStatus.RUNNING
    assert jobs[0].component == ComponentType.FLINK
