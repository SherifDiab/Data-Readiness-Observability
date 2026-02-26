"""
Shared httpx.AsyncClient with retry logic and configurable timeouts.
Used by all IBM service pollers.
"""

import logging

import httpx

logger = logging.getLogger(__name__)

_client: httpx.AsyncClient | None = None


async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        transport = httpx.AsyncHTTPTransport(retries=3, verify=False)
        _client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
        )
    return _client


async def close_http_client():
    global _client
    if _client:
        await _client.aclose()
        _client = None
