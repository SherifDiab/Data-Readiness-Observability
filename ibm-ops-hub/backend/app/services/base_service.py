"""
Abstract base service for all IBM component pollers.

Every concrete service (Spark, DataStage, Flink, Event Processing, APIC)
inherits from BaseService and implements ``poll()`` and ``get_health()``.
The base class provides shared infrastructure: HTTP client, Redis caching,
structured logging, and a common serialisation helper.
"""

from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from typing import Any

import httpx
import redis.asyncio as aioredis

from app.config import Settings
from app.schemas import NormalizedJob, ComponentHealth
from app.cache import DateTimeEncoder


class BaseService(ABC):
    """Base class that all IBM service pollers extend.

    Parameters
    ----------
    settings : Settings
        Application configuration loaded from environment / .env file.
    redis : aioredis.Redis
        Async Redis client used for caching poll results and auth tokens.
    http_client : httpx.AsyncClient
        Shared async HTTP client with retry/timeout configuration.
    """

    def __init__(
        self,
        settings: Settings,
        redis: aioredis.Redis,
        http_client: httpx.AsyncClient,
    ):
        self.settings = settings
        self.redis = redis
        self.client = http_client
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Abstract interface — every service MUST implement these
    # ------------------------------------------------------------------

    @abstractmethod
    async def poll(self) -> list[NormalizedJob]:
        """Poll the external service and return normalised job data.

        Returns
        -------
        list[NormalizedJob]
            A list of jobs normalised into the common schema.
        """
        ...

    @abstractmethod
    async def get_health(self) -> ComponentHealth:
        """Compute and return a health summary for this component.

        Returns
        -------
        ComponentHealth
            Aggregated counts (running, failed, completed, …) and reachability.
        """
        ...

    # ------------------------------------------------------------------
    # Shared caching helpers
    # ------------------------------------------------------------------

    async def cache_results(self, key: str, data: list, ttl: int = 120) -> None:
        """Serialise a list of Pydantic models (or dicts) into Redis.

        Parameters
        ----------
        key : str
            Redis key under which the data is stored.
        data : list
            Items to cache — may be Pydantic ``BaseModel`` instances or plain dicts.
        ttl : int
            Time-to-live in seconds (default 120).
        """
        serialized = json.dumps(
            [d.model_dump() if hasattr(d, "model_dump") else d for d in data],
            cls=DateTimeEncoder,
        )
        await self.redis.set(key, serialized, ex=ttl)

    async def get_cached(self, key: str) -> list[dict] | None:
        """Retrieve previously-cached data from Redis.

        Parameters
        ----------
        key : str
            Redis key to look up.

        Returns
        -------
        list[dict] | None
            Deserialised list of dicts, or ``None`` if the key does not exist
            or has expired.
        """
        raw = await self.redis.get(key)
        if raw is None:
            return None
        return json.loads(raw)
