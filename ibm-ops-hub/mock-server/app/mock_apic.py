"""
Mock IBM API Connect Analytics API.
Generates realistic API call logs with varying status codes and latencies.
"""

import random
import time
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Path, Query

router = APIRouter()

API_NAMES = ["Customer API", "Order API", "Product API", "Payment API", "Inventory API"]
API_PATHS = {
    "Customer API": ["/customers", "/customers/{id}", "/customers/{id}/profile", "/customers/search"],
    "Order API": ["/orders", "/orders/{id}", "/orders/{id}/status", "/orders/{id}/items"],
    "Product API": ["/products", "/products/{id}", "/products/search", "/products/categories"],
    "Payment API": ["/payments", "/payments/{id}", "/payments/refunds", "/payments/methods"],
    "Inventory API": ["/inventory", "/inventory/{sku}", "/inventory/alerts", "/inventory/warehouses"],
}
METHODS = ["GET", "GET", "GET", "POST", "PUT", "DELETE"]
CONSUMER_ORGS = ["acme-corp", "beta-solutions", "gamma-tech", "delta-finance", "omega-retail"]
ERROR_CODES = [400, 401, 403, 404, 429, 500, 502, 503]


def _generate_events(timeframe_hours: float, limit: int = 500) -> list[dict]:
    rng = random.Random(int(time.time() // 300))
    events = []
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=timeframe_hours)

    for _ in range(min(limit, 500)):
        api_name = rng.choice(API_NAMES)
        paths = API_PATHS[api_name]
        method = rng.choice(METHODS)
        ts = start + timedelta(seconds=rng.uniform(0, timeframe_hours * 3600))

        # ~15% error rate
        if rng.random() < 0.15:
            status_code = rng.choice(ERROR_CODES)
            latency = rng.uniform(200, 5000)
        else:
            status_code = 200 if method == "GET" else (201 if method == "POST" else 200)
            latency = rng.expovariate(1 / 80)  # avg 80ms
            latency = min(latency, 2000)

        events.append({
            "datetime": ts.isoformat(),
            "api_name": api_name,
            "api_version": "1.0.0",
            "request_method": method,
            "uri_path": rng.choice(paths),
            "status_code": status_code,
            "time_to_serve_request": round(latency, 2),
            "developer_org_name": rng.choice(CONSUMER_ORGS),
            "app_name": f"app-{rng.randint(1, 20)}",
            "client_ip": f"10.{rng.randint(1,254)}.{rng.randint(1,254)}.{rng.randint(1,254)}",
            "bytes_received": rng.randint(100, 10000),
            "bytes_sent": rng.randint(200, 50000),
        })

    events.sort(key=lambda e: e["datetime"], reverse=True)
    return events


TIMEFRAME_HOURS = {
    "last15m": 0.25,
    "last1hour": 1.0,
    "last6hours": 6.0,
    "last24hours": 24.0,
}


@router.post("/api/token")
async def get_apic_token():
    return {
        "access_token": "mock-apic-token-abc123xyz",
        "token_type": "bearer",
        "expires_in": 28800,
    }


@router.get("/analytics/{org}/{catalog}/events")
async def get_events(
    org: str = Path(...),
    catalog: str = Path(...),
    timeframe: str = Query("last1hour"),
    limit: int = Query(500),
):
    hours = TIMEFRAME_HOURS.get(timeframe, 1.0)
    events = _generate_events(hours, limit)
    return {"events": events, "count": len(events)}
