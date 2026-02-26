"""
Test configuration and shared fixtures.
"""

import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
import pytest_asyncio
import redis.asyncio as aioredis

from app.config import Settings

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


@pytest.fixture
def test_settings():
    return Settings(
        CPD_BASE_URL="http://mock-server:9000",
        CPD_USERNAME="test",
        CPD_PASSWORD="test",
        CPD_PROJECT_ID="test-project",
        FLINK_REST_URL="http://mock-server:9000",
        APIC_MGMT_URL="http://mock-server:9000",
        APIC_ANALYTICS_URL="http://mock-server:9000",
        APIC_ORG="testorg",
        APIC_CATALOG="testcatalog",
        APIC_USERNAME="test",
        APIC_PASSWORD="test",
        REDIS_URL="redis://localhost:6379/0",
        DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/opshub_test",
        MOCK_MODE=True,
        MOCK_SERVER_URL="http://mock-server:9000",
    )


@pytest.fixture
def mock_redis():
    r = MagicMock(spec=aioredis.Redis)
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock(return_value=True)
    return r


@pytest.fixture
def mock_http_client():
    return AsyncMock(spec=httpx.AsyncClient)
