"""
Authentication service for IBM Cloud Pak for Data and API Connect.

Manages token acquisition and Redis-based caching so that multiple pollers
can share a single valid token without redundant auth round-trips.

Token flow
----------
CPD token:
    POST {CPD_BASE_URL}/icp4d-api/v1/authorize
    Body: {"username": "...", "password": "..."}
    Response: {"token": "<bearer-token>"}

APIC token:
    POST {APIC_MGMT_URL}/api/token
    Body: {"username": "...", "password": "...", "realm": "...", "grant_type": "password"}
    Response: {"access_token": "<bearer-token>", "expires_in": 28800}
"""

import json
import logging
from typing import Any

import httpx
import redis.asyncio as aioredis

from app.config import Settings

logger = logging.getLogger(__name__)

# Redis key constants
CPD_TOKEN_KEY = "auth:cpd_token"
APIC_TOKEN_KEY = "auth:apic_token"

# Default TTLs (seconds) — slightly shorter than actual expiry to avoid races
CPD_TOKEN_TTL = 3300  # CPD tokens typically last ~1 h; refresh at 55 min
APIC_TOKEN_TTL = 28000  # APIC tokens typically last 8 h; refresh a bit early


class AuthService:
    """Centralised token manager used by Spark, DataStage, and APIC services.

    Parameters
    ----------
    settings : Settings
        Application configuration.
    redis : aioredis.Redis
        Async Redis client for token caching.
    http_client : httpx.AsyncClient
        Shared HTTP client.
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

    # ------------------------------------------------------------------
    # Cloud Pak for Data token
    # ------------------------------------------------------------------

    async def get_cpd_token(self) -> str:
        """Return a valid CPD bearer token, fetching a new one if the cache is empty.

        Request shape
        -------------
        POST {CPD_BASE_URL}/icp4d-api/v1/authorize
        Content-Type: application/json
        {
            "username": "<CPD_USERNAME>",
            "password": "<CPD_PASSWORD>"
        }

        Response shape
        --------------
        200 OK
        {
            "_messageCode_": "200",
            "message": "success",
            "token": "<jwt-bearer-token>"
        }

        Returns
        -------
        str
            Bearer token string.

        Raises
        ------
        httpx.HTTPStatusError
            If the auth endpoint returns a non-2xx status.
        """
        # 1. Check Redis cache first
        cached = await self.redis.get(CPD_TOKEN_KEY)
        if cached:
            logger.debug("CPD token retrieved from cache")
            return cached

        # 2. Determine base URL (mock vs. real)
        base_url = (
            self.settings.MOCK_SERVER_URL
            if self.settings.MOCK_MODE
            else self.settings.CPD_BASE_URL
        )
        url = f"{base_url}/icp4d-api/v1/authorize"

        logger.info("Requesting new CPD token from %s", url)
        try:
            response = await self.client.post(
                url,
                json={
                    "username": self.settings.CPD_USERNAME,
                    "password": self.settings.CPD_PASSWORD,
                },
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            token = data["token"]

            # 3. Cache the token in Redis
            await self.redis.set(CPD_TOKEN_KEY, token, ex=CPD_TOKEN_TTL)
            logger.info("CPD token acquired and cached (TTL=%ds)", CPD_TOKEN_TTL)
            return token

        except httpx.HTTPStatusError as exc:
            logger.error(
                "CPD auth failed — endpoint=%s status=%s body=%s",
                url,
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise
        except Exception as exc:
            logger.error("CPD auth request error — endpoint=%s error=%s", url, exc)
            raise

    # ------------------------------------------------------------------
    # API Connect token
    # ------------------------------------------------------------------

    async def get_apic_token(self) -> str:
        """Return a valid APIC bearer token, fetching a new one if the cache is empty.

        Request shape
        -------------
        POST {APIC_MGMT_URL}/api/token
        Content-Type: application/json
        {
            "username": "<APIC_USERNAME>",
            "password": "<APIC_PASSWORD>",
            "realm": "<APIC_REALM>",
            "grant_type": "password"
        }

        Response shape
        --------------
        200 OK
        {
            "access_token": "<bearer-token>",
            "token_type": "Bearer",
            "expires_in": 28800
        }

        Returns
        -------
        str
            Bearer token string.

        Raises
        ------
        httpx.HTTPStatusError
            If the auth endpoint returns a non-2xx status.
        """
        # 1. Check Redis cache first
        cached = await self.redis.get(APIC_TOKEN_KEY)
        if cached:
            logger.debug("APIC token retrieved from cache")
            return cached

        # 2. Determine base URL (mock vs. real)
        base_url = (
            self.settings.MOCK_SERVER_URL
            if self.settings.MOCK_MODE
            else self.settings.APIC_MGMT_URL
        )
        url = f"{base_url}/api/token"

        logger.info("Requesting new APIC token from %s", url)
        try:
            response = await self.client.post(
                url,
                json={
                    "username": self.settings.APIC_USERNAME,
                    "password": self.settings.APIC_PASSWORD,
                    "realm": self.settings.APIC_REALM,
                    "grant_type": "password",
                },
            )
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            token = data["access_token"]

            # Use the server-supplied expiry if available, minus a small buffer
            ttl = min(int(data.get("expires_in", APIC_TOKEN_TTL)) - 300, APIC_TOKEN_TTL)
            ttl = max(ttl, 60)  # at least 60 s

            # 3. Cache the token in Redis
            await self.redis.set(APIC_TOKEN_KEY, token, ex=ttl)
            logger.info("APIC token acquired and cached (TTL=%ds)", ttl)
            return token

        except httpx.HTTPStatusError as exc:
            logger.error(
                "APIC auth failed — endpoint=%s status=%s body=%s",
                url,
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise
        except Exception as exc:
            logger.error("APIC auth request error — endpoint=%s error=%s", url, exc)
            raise

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def invalidate_cpd_token(self) -> None:
        """Remove the cached CPD token, forcing a fresh auth on the next call."""
        await self.redis.delete(CPD_TOKEN_KEY)
        logger.info("CPD token cache invalidated")

    async def invalidate_apic_token(self) -> None:
        """Remove the cached APIC token, forcing a fresh auth on the next call."""
        await self.redis.delete(APIC_TOKEN_KEY)
        logger.info("APIC token cache invalidated")
