"""
Tests for SparkService.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import ComponentType, JobStatus
from app.services.auth_service import AuthService
from app.services.spark_service import SparkService


@pytest.fixture
def auth_service(test_settings, mock_redis, mock_http_client):
    auth = MagicMock(spec=AuthService)
    auth.get_cpd_token = AsyncMock(return_value="mock-cpd-token")
    return auth


@pytest.fixture
def spark_service(test_settings, mock_redis, mock_http_client, auth_service):
    # SparkService takes auth_service as first positional arg (before base class args)
    return SparkService(auth_service, test_settings, mock_redis, mock_http_client)


def test_status_mapping(spark_service):
    assert spark_service._map_state("Running") == JobStatus.RUNNING
    assert spark_service._map_state("Completed") == JobStatus.COMPLETED
    assert spark_service._map_state("Failed") == JobStatus.FAILED
    assert spark_service._map_state("Queued") == JobStatus.QUEUED
    assert spark_service._map_state("Starting") == JobStatus.STARTING
    assert spark_service._map_state("Canceled") == JobStatus.CANCELED
    assert spark_service._map_state(None) == JobStatus.UNKNOWN


@pytest.mark.asyncio
async def test_poll_with_mock_server(spark_service):
    jobs_response = {
        "resources": [
            {
                "metadata": {"asset_id": "job-001", "name": "Test_Spark_Job"},
                "entity": {"job": {"asset_ref": "ref-001", "asset_ref_type": "notebook"}}
            }
        ],
        "total_count": 1,
    }
    runs_response = {
        "resources": [
            {
                "metadata": {"asset_id": "run-001"},
                "entity": {
                    "job_run": {
                        "state": "Running",
                        "started_at": "2026-02-26T10:00:00Z",
                        "finished_at": None,
                        "duration": None,
                    }
                }
            }
        ]
    }

    def mock_get(url, **kwargs):
        resp = MagicMock(spec=httpx.Response)
        resp.raise_for_status = MagicMock()
        if "/runs" in url:
            resp.json.return_value = runs_response
        else:
            resp.json.return_value = jobs_response
        return resp

    spark_service.client.get = AsyncMock(side_effect=mock_get)
    spark_service.redis.set = AsyncMock()

    jobs = await spark_service.poll()
    assert len(jobs) == 1
    assert jobs[0].job_name == "Test_Spark_Job"
    assert jobs[0].status == JobStatus.RUNNING
    assert jobs[0].component == ComponentType.SPARK
