"""
Tests for DataStageService.
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.schemas import ComponentType, JobStatus
from app.services.auth_service import AuthService
from app.services.datastage_service import DataStageService


@pytest.fixture
def auth_service(test_settings, mock_redis, mock_http_client):
    auth = MagicMock(spec=AuthService)
    auth.get_cpd_token = AsyncMock(return_value="mock-cpd-token")
    return auth


@pytest.fixture
def ds_service(test_settings, mock_redis, mock_http_client, auth_service):
    return DataStageService(auth_service, test_settings, mock_redis, mock_http_client)


def test_iis_status_mapping(ds_service):
    assert ds_service._map_iis_state(0) == JobStatus.RUNNING
    assert ds_service._map_iis_state(1) == JobStatus.COMPLETED
    assert ds_service._map_iis_state(2) == JobStatus.WARNING
    assert ds_service._map_iis_state(3) == JobStatus.FAILED
    assert ds_service._map_iis_state(96) == JobStatus.FAILED
    assert ds_service._map_iis_state(97) == JobStatus.CANCELED


@pytest.mark.asyncio
async def test_poll_cpd_mode(ds_service):
    jobs_response = {
        "resources": [
            {
                "metadata": {"asset_id": "ds-job-001", "name": "DS_Customer_Transform"},
                "entity": {"job": {"asset_ref": "flow-ref-001", "asset_ref_type": "data_intg_flow"}}
            }
        ],
        "total_count": 1,
    }
    runs_response = {
        "resources": [
            {
                "metadata": {"asset_id": "ds-run-001"},
                "entity": {
                    "job_run": {
                        "state": "Completed",
                        "started_at": "2026-02-26T09:00:00Z",
                        "finished_at": "2026-02-26T09:30:00Z",
                        "duration": 1800,
                        "rows_read": 50000,
                        "rows_written": 49980,
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

    ds_service.client.get = AsyncMock(side_effect=mock_get)
    ds_service.redis.set = AsyncMock()

    jobs = await ds_service.poll()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.COMPLETED
    assert jobs[0].component == ComponentType.DATASTAGE
