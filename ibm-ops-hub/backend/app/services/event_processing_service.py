"""
Event Processing Service — polls Kubernetes API for IBM Event Processing flows
running as FlinkDeployment Custom Resources.

K8s API endpoint:
  GET /apis/flink.apache.org/v1beta1/namespaces/{namespace}/flinkdeployments

Each FlinkDeployment CR contains:
  - metadata.name / metadata.uid
  - status.jobStatus.state: RUNNING | FINISHED | FAILED | CANCELED | SUSPENDED | RECONCILING
  - status.jobManagerDeploymentStatus: READY | DEPLOYING | ERROR | MISSING
  - status.reconciliationStatus.state: DEPLOYED | UPGRADING | ROLLING_BACK
  - spec.job.state: running | suspended (desired state)
  - status.jobStatus.startTime
  - status.jobStatus.savepointInfo.lastPeriodicSavepointTimestamp

In MOCK_MODE, uses HTTP GET to mock-server instead of real K8s client.
"""

import logging
from datetime import datetime, timezone

import httpx

from app.config import Settings
from app.schemas import ComponentHealth, ComponentType, JobStatus, NormalizedJob
from app.services.base_service import BaseService
from app.utils.normalize import compute_health

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

FLINK_STATE_MAP = {
    "RUNNING": JobStatus.RUNNING,
    "FINISHED": JobStatus.COMPLETED,
    "FAILED": JobStatus.FAILED,
    "CANCELED": JobStatus.CANCELED,
    "SUSPENDED": JobStatus.SUSPENDED,
    "RECONCILING": JobStatus.RESTARTING,
}

CACHE_KEY = "event_processing:flows"


class EventProcessingService(BaseService):
    """Polls Kubernetes for IBM Event Processing FlinkDeployment CRDs."""

    def __init__(self, settings: Settings, redis: aioredis.Redis, http_client: httpx.AsyncClient):
        super().__init__(settings, redis, http_client)

    async def poll(self) -> list[NormalizedJob]:
        """Fetch FlinkDeployment statuses from K8s (or mock server)."""
        try:
            if self.settings.MOCK_MODE:
                return await self._poll_mock()
            return await self._poll_k8s()
        except Exception as e:
            self.logger.error("EventProcessing poll failed: %s", e)
            cached = await self.get_cached(CACHE_KEY)
            if cached:
                return [NormalizedJob(**j) for j in cached]
            return []

    async def _poll_mock(self) -> list[NormalizedJob]:
        ns = self.settings.K8S_NAMESPACE
        url = (
            f"{self.settings.MOCK_SERVER_URL}/apis/{self.settings.FLINK_CRD_GROUP}"
            f"/{self.settings.FLINK_CRD_VERSION}/namespaces/{ns}/flinkdeployments"
        )
        self.logger.info("EventProcessing: GET %s", url)
        resp = await self.client.get(url)
        resp.raise_for_status()
        data = resp.json()
        jobs = [self._parse_cr(item) for item in data.get("items", [])]
        await self.cache_results(CACHE_KEY, [j.model_dump(mode="json") for j in jobs])
        return jobs

    async def _poll_k8s(self) -> list[NormalizedJob]:
        """Use kubernetes-asyncio client to list FlinkDeployment CRs."""
        try:
            from kubernetes_asyncio import client, config  # type: ignore
            if self.settings.K8S_IN_CLUSTER:
                await config.load_incluster_config()
            else:
                await config.load_kube_config(config_file=self.settings.K8S_KUBECONFIG or None)

            async with client.ApiClient() as api_client:
                custom_api = client.CustomObjectsApi(api_client)
                result = await custom_api.list_namespaced_custom_object(
                    group=self.settings.FLINK_CRD_GROUP,
                    version=self.settings.FLINK_CRD_VERSION,
                    namespace=self.settings.K8S_NAMESPACE,
                    plural="flinkdeployments",
                )
            jobs = [self._parse_cr(item) for item in result.get("items", [])]
            await self.cache_results(CACHE_KEY, [j.model_dump(mode="json") for j in jobs])
            return jobs
        except ImportError:
            self.logger.warning("kubernetes-asyncio not available, using mock")
            return await self._poll_mock()

    def _parse_cr(self, item: dict) -> NormalizedJob:
        metadata = item.get("metadata", {})
        status = item.get("status", {})
        job_status = status.get("jobStatus", {})
        spec = item.get("spec", {})

        raw_state = (job_status.get("state") or "").upper()
        normalized = FLINK_STATE_MAP.get(raw_state, JobStatus.UNKNOWN)

        start_time = job_status.get("startTime")
        started_at = None
        if start_time:
            try:
                started_at = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except Exception:
                pass

        savepoint_info = job_status.get("savepointInfo", {})
        last_savepoint_ts = savepoint_info.get("lastPeriodicSavepointTimestamp") if savepoint_info else None

        return NormalizedJob(
            component=ComponentType.EVENT_PROCESSING,
            job_id=metadata.get("uid", metadata.get("name", "unknown")),
            job_name=metadata.get("name", "unknown"),
            status=normalized,
            started_at=started_at,
            finished_at=None,
            duration_seconds=None,
            details={
                "jm_deployment_status": status.get("jobManagerDeploymentStatus"),
                "reconciliation_status": (status.get("reconciliationStatus") or {}).get("state"),
                "desired_state": (spec.get("job") or {}).get("state"),
                "parallelism": (spec.get("job") or {}).get("parallelism"),
                "flink_image": (spec.get("image") or None),
                "last_savepoint_timestamp": str(last_savepoint_ts) if last_savepoint_ts else None,
                "namespace": metadata.get("namespace"),
            },
            last_polled_at=datetime.now(timezone.utc),
        )

    async def get_health(self) -> ComponentHealth:
        cached = await self.get_cached(CACHE_KEY)
        if cached:
            jobs = [NormalizedJob(**j) for j in cached]
            return compute_health(ComponentType.EVENT_PROCESSING, jobs)
        return compute_health(ComponentType.EVENT_PROCESSING, [], is_reachable=False, error_message="No data cached")
