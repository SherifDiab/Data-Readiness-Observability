"""
Flink service poller for standalone Apache Flink clusters.

Communicates with the Flink REST API (typically exposed by the JobManager on
port 8081) to retrieve job statuses, checkpoint statistics, and cluster
overview data.

Flink REST API reference
------------------------
Jobs overview:
    GET {FLINK_REST_URL}/jobs/overview
    Response:
    {
        "jobs": [
            {
                "jid": "abc123...",
                "name": "my-flink-job",
                "state": "RUNNING",
                "start-time": 1700000000000,
                "end-time": -1,
                "duration": 120000,
                "last-modification": 1700000001000,
                "tasks": {"total": 4, "running": 4, ...}
            },
            ...
        ]
    }

Job exceptions:
    GET {FLINK_REST_URL}/jobs/{jid}/exceptions
    Response:
    {
        "root-exception": "java.lang.RuntimeException: ...",
        "all-exceptions": [
            {"exception": "...", "task": "...", "location": "..."}
        ],
        "truncated": false
    }

Job checkpoints:
    GET {FLINK_REST_URL}/jobs/{jid}/checkpoints
    Response:
    {
        "counts": {"completed": 10, "failed": 0, "in_progress": 0, "restored": 1, "total": 10},
        "latest": {
            "completed": {"id": 10, "duration": 345, "size": 12345678, ...},
            "restored": {"id": 9, ...}
        },
        "history": [...]
    }

Cluster overview:
    GET {FLINK_REST_URL}/overview
    Response:
    {
        "taskmanagers": 3,
        "slots-total": 12,
        "slots-available": 4,
        "jobs-running": 2,
        "jobs-finished": 5,
        "jobs-cancelled": 1,
        "jobs-failed": 0,
        "flink-version": "1.18.1",
        "flink-commit": "..."
    }
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.schemas import (
    ComponentHealth,
    ComponentType,
    FlinkClusterOverview,
    JobStatus,
    NormalizedJob,
)
from app.utils.normalize import compute_health, epoch_ms_to_datetime
from app.services.base_service import BaseService

logger = logging.getLogger(__name__)

# Flink state -> JobStatus mapping
_FLINK_STATE_MAP: dict[str, JobStatus] = {
    "CREATED": JobStatus.QUEUED,
    "INITIALIZING": JobStatus.STARTING,
    "RUNNING": JobStatus.RUNNING,
    "FINISHED": JobStatus.COMPLETED,
    "CANCELLING": JobStatus.CANCELED,
    "CANCELED": JobStatus.CANCELED,
    "FAILING": JobStatus.FAILED,
    "FAILED": JobStatus.FAILED,
    "RESTARTING": JobStatus.RESTARTING,
    "SUSPENDED": JobStatus.SUSPENDED,
    "RECONCILING": JobStatus.RESTARTING,
}

CACHE_KEY_JOBS = "flink:jobs"
CACHE_KEY_CLUSTER = "flink:cluster"


class FlinkService(BaseService):
    """Polls standalone Apache Flink clusters via the REST API."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        """Return the Flink REST URL, switching to mock server when enabled."""
        if self.settings.MOCK_MODE:
            return self.settings.MOCK_SERVER_URL
        return self.settings.FLINK_REST_URL

    @staticmethod
    def _map_state(flink_state: str | None) -> JobStatus:
        """Map a Flink job state string to the normalised ``JobStatus`` enum."""
        if flink_state is None:
            return JobStatus.UNKNOWN
        return _FLINK_STATE_MAP.get(flink_state.upper(), JobStatus.UNKNOWN)

    # ------------------------------------------------------------------
    # Enrichment helpers
    # ------------------------------------------------------------------

    async def _fetch_exceptions(self, jid: str) -> dict[str, Any]:
        """Fetch exception details for a failed/failing Flink job.

        Parameters
        ----------
        jid : str
            Flink job ID.

        Returns
        -------
        dict
            Exception details including root exception text.
        """
        url = f"{self._base_url()}/jobs/{jid}/exceptions"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            return {
                "root_exception": data.get("root-exception", "")[:1000],
                "truncated": data.get("truncated", False),
            }
        except Exception as exc:
            self.logger.warning(
                "Flink — failed to fetch exceptions for job=%s endpoint=%s error=%s",
                jid,
                url,
                exc,
            )
            return {}

    async def _fetch_checkpoints(self, jid: str) -> dict[str, Any]:
        """Fetch checkpoint statistics for a running Flink job.

        Parameters
        ----------
        jid : str
            Flink job ID.

        Returns
        -------
        dict
            Checkpoint counts and latest checkpoint metadata.
        """
        url = f"{self._base_url()}/jobs/{jid}/checkpoints"
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data = resp.json()
            counts = data.get("counts", {})
            latest_completed = (data.get("latest") or {}).get("completed", {})
            return {
                "checkpoints_completed": counts.get("completed", 0),
                "checkpoints_failed": counts.get("failed", 0),
                "checkpoints_in_progress": counts.get("in_progress", 0),
                "checkpoints_total": counts.get("total", 0),
                "latest_checkpoint_duration_ms": latest_completed.get("duration"),
                "latest_checkpoint_size_bytes": latest_completed.get("size"),
            }
        except Exception as exc:
            self.logger.warning(
                "Flink — failed to fetch checkpoints for job=%s endpoint=%s error=%s",
                jid,
                url,
                exc,
            )
            return {}

    # ------------------------------------------------------------------
    # Core polling
    # ------------------------------------------------------------------

    async def poll(self) -> list[NormalizedJob]:
        """Fetch all jobs from the Flink REST API and enrich with exceptions/checkpoints.

        Returns
        -------
        list[NormalizedJob]
            Normalised Flink jobs.
        """
        now = datetime.now(timezone.utc)
        base = self._base_url()
        jobs: list[NormalizedJob] = []

        try:
            url = f"{base}/jobs/overview"
            self.logger.info("Flink poll — GET %s", url)
            resp = await self.client.get(url)
            resp.raise_for_status()
            job_list: list[dict] = resp.json().get("jobs", [])

            for entry in job_list:
                jid: str = entry.get("jid", "")
                name: str = entry.get("name", "unknown")
                state_str: str | None = entry.get("state")
                status = self._map_state(state_str)

                started = epoch_ms_to_datetime(entry.get("start-time"))
                finished = epoch_ms_to_datetime(entry.get("end-time"))
                duration_ms = entry.get("duration")
                duration_s = duration_ms / 1000.0 if duration_ms and duration_ms > 0 else None

                tasks = entry.get("tasks", {})
                details: dict[str, Any] = {
                    "flink_state": state_str,
                    "tasks_total": tasks.get("total", 0),
                    "tasks_running": tasks.get("running", 0),
                    "tasks_finished": tasks.get("finished", 0),
                    "tasks_failed": tasks.get("failed", 0),
                }

                # Enrich failed jobs with exception info
                if status == JobStatus.FAILED:
                    exc_info = await self._fetch_exceptions(jid)
                    details.update(exc_info)

                # Enrich running jobs with checkpoint info
                if status == JobStatus.RUNNING:
                    cp_info = await self._fetch_checkpoints(jid)
                    details.update(cp_info)

                native_url = f"{self.settings.FLINK_REST_URL}/#/jobs/{jid}"

                jobs.append(
                    NormalizedJob(
                        component=ComponentType.FLINK,
                        job_id=jid,
                        job_name=name,
                        status=status,
                        started_at=started,
                        finished_at=finished,
                        duration_seconds=duration_s,
                        details=details,
                        native_url=native_url,
                        last_polled_at=now,
                    )
                )

            await self.cache_results(
                CACHE_KEY_JOBS, jobs, ttl=self.settings.FLINK_POLL_INTERVAL * 4
            )
            self.logger.info("Flink poll complete — %d jobs normalised", len(jobs))

        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "Flink poll failed — endpoint=%s status=%s body=%s",
                exc.request.url,
                exc.response.status_code,
                exc.response.text[:500],
            )
        except Exception as exc:
            self.logger.error("Flink poll error — %s", exc, exc_info=True)

        return jobs

    # ------------------------------------------------------------------
    # Cluster overview
    # ------------------------------------------------------------------

    async def get_cluster_overview(self) -> FlinkClusterOverview:
        """Fetch the Flink cluster overview and return a typed model.

        Request
        -------
        GET {FLINK_REST_URL}/overview

        Returns
        -------
        FlinkClusterOverview
            Structured cluster metrics (taskmanagers, slots, job counts, version).

        Raises
        ------
        httpx.HTTPStatusError
            If the endpoint returns a non-2xx response.
        """
        url = f"{self._base_url()}/overview"
        self.logger.info("Flink cluster overview — GET %s", url)

        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            data: dict[str, Any] = resp.json()

            overview = FlinkClusterOverview(
                taskmanagers=data.get("taskmanagers", 0),
                slots_total=data.get("slots-total", 0),
                slots_available=data.get("slots-available", 0),
                jobs_running=data.get("jobs-running", 0),
                jobs_finished=data.get("jobs-finished", 0),
                jobs_cancelled=data.get("jobs-cancelled", 0),
                jobs_failed=data.get("jobs-failed", 0),
                flink_version=data.get("flink-version", "unknown"),
            )

            # Cache the cluster overview as a single-element list
            await self.cache_results(
                CACHE_KEY_CLUSTER,
                [overview],
                ttl=self.settings.FLINK_POLL_INTERVAL * 4,
            )
            return overview

        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "Flink cluster overview failed — endpoint=%s status=%s body=%s",
                url,
                exc.response.status_code,
                exc.response.text[:500],
            )
            raise
        except Exception as exc:
            self.logger.error("Flink cluster overview error — %s", exc, exc_info=True)
            raise

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def get_health(self) -> ComponentHealth:
        """Compute health from the most recent cached Flink jobs.

        Returns
        -------
        ComponentHealth
            Aggregated status counts and reachability indicator.
        """
        cached = await self.get_cached(CACHE_KEY_JOBS)
        if cached is not None:
            normalised = [NormalizedJob(**j) for j in cached]
            return compute_health(ComponentType.FLINK, normalised, is_reachable=True)

        try:
            fresh = await self.poll()
            return compute_health(ComponentType.FLINK, fresh, is_reachable=True)
        except Exception as exc:
            self.logger.error("Flink health check failed — %s", exc)
            return compute_health(
                ComponentType.FLINK,
                [],
                is_reachable=False,
                error_message=str(exc),
            )
