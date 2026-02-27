"""
Spark service poller for IBM Cloud Pak for Data (CPD) analytics jobs.

Authenticates with CPD, fetches all Spark jobs in the configured project,
then retrieves recent runs for each job. Results are normalised into the
common ``NormalizedJob`` schema and cached in Redis.

CPD API reference
-----------------
List jobs:
    GET {CPD_BASE_URL}/v2/jobs?project_id={pid}&limit=100
    Authorization: Bearer <cpd-token>
    Response:
    {
        "results": [
            {
                "metadata": {"asset_id": "...", "name": "...", "asset_ref_type": "..."},
                "entity": {"job": {"last_run_status": "...", ...}}
            },
            ...
        ],
        "total_results": 42
    }

List runs for a job:
    GET {CPD_BASE_URL}/v2/jobs/{job_id}/runs?project_id={pid}&limit=5
    Authorization: Bearer <cpd-token>
    Response:
    {
        "results": [
            {
                "metadata": {"asset_id": "<run_id>"},
                "entity": {
                    "job_run": {
                        "state": "Completed|Failed|Running|...",
                        "start_timestamp": "2025-01-01T00:00:00Z",
                        "end_timestamp": "2025-01-01T00:10:00Z",
                        "duration": 600
                    }
                }
            },
            ...
        ]
    }
"""

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from app.schemas import ComponentHealth, ComponentType, JobStatus, NormalizedJob
from app.utils.normalize import compute_health
from app.services.base_service import BaseService
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

# CPD state -> JobStatus mapping
_CPD_STATE_MAP: dict[str, JobStatus] = {
    "Running": JobStatus.RUNNING,
    "Completed": JobStatus.COMPLETED,
    "Failed": JobStatus.FAILED,
    "Canceled": JobStatus.CANCELED,
    "Cancelled": JobStatus.CANCELED,
    "Starting": JobStatus.STARTING,
    "Queued": JobStatus.QUEUED,
    "Paused": JobStatus.SUSPENDED,
    "CompletedWithWarnings": JobStatus.WARNING,
}

CACHE_KEY = "spark:jobs"


class SparkService(BaseService):
    """Polls IBM Cloud Pak for Data Spark analytics jobs.

    Parameters
    ----------
    auth_service : AuthService
        Shared authentication service for obtaining CPD bearer tokens.
    *args, **kwargs
        Forwarded to ``BaseService.__init__``.
    """

    def __init__(self, auth_service: AuthService, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.auth_service = auth_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _base_url(self) -> str:
        """Return the CPD base URL, switching to mock server when enabled."""
        if self.settings.MOCK_MODE:
            return self.settings.MOCK_SERVER_URL
        return self.settings.CPD_BASE_URL

    @staticmethod
    def _map_state(cpd_state: str | None) -> JobStatus:
        """Map a CPD run state string to the normalised ``JobStatus`` enum."""
        if cpd_state is None:
            return JobStatus.UNKNOWN
        return _CPD_STATE_MAP.get(cpd_state, JobStatus.UNKNOWN)

    @staticmethod
    def _parse_ts(ts_str: str | None) -> datetime | None:
        """Safely parse an ISO-8601 timestamp from CPD."""
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Core polling
    # ------------------------------------------------------------------

    async def poll(self) -> list[NormalizedJob]:
        """Fetch Spark jobs across all configured CPD projects.

        Iterates over every project in ``settings.cpd_project_ids_list``,
        queries the CPD Jobs API, and fetches the latest run for each job.
        Job IDs are scoped as ``{project_id}/{asset_id}`` to prevent collisions
        across projects.

        Returns
        -------
        list[NormalizedJob]
            Normalised jobs with the latest run status from all projects.
        """
        now = datetime.now(timezone.utc)
        base = self._base_url()
        all_jobs: list[NormalizedJob] = []

        try:
            token = await self.auth_service.get_cpd_token()
            headers = {"Authorization": f"Bearer {token}"}
            project_ids = self.settings.cpd_project_ids_list

            self.logger.info(
                "Spark poll — monitoring %d project(s): %s", len(project_ids), project_ids
            )

            for project_id in project_ids:
                try:
                    project_jobs = await self._poll_project(base, project_id, headers, now)
                    all_jobs.extend(project_jobs)
                    self.logger.info(
                        "Spark poll — project=%s yielded %d jobs", project_id, len(project_jobs)
                    )
                except Exception as exc:
                    self.logger.error(
                        "Spark poll — project=%s failed: %s", project_id, exc
                    )

            await self.cache_results(CACHE_KEY, all_jobs, ttl=self.settings.SPARK_POLL_INTERVAL * 4)
            self.logger.info(
                "Spark poll complete — %d total jobs across %d project(s)",
                len(all_jobs), len(project_ids),
            )

        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "Spark poll failed — endpoint=%s status=%s body=%s",
                exc.request.url, exc.response.status_code, exc.response.text[:500],
            )
        except Exception as exc:
            self.logger.error("Spark poll error — %s", exc, exc_info=True)

        return all_jobs

    async def _poll_project(
        self,
        base: str,
        project_id: str,
        headers: dict[str, str],
        now: datetime,
    ) -> list[NormalizedJob]:
        """Poll a single CPD project for Spark jobs."""
        jobs: list[NormalizedJob] = []
        jobs_url = f"{base}/v2/jobs"
        params: dict[str, Any] = {"project_id": project_id, "limit": 100}

        self.logger.info("Spark — GET %s project=%s", jobs_url, project_id)
        resp = await self.client.get(jobs_url, headers=headers, params=params)
        resp.raise_for_status()
        job_list: list[dict] = resp.json().get("results", [])

        for job_entry in job_list:
            metadata = job_entry.get("metadata", {})
            asset_id = metadata.get("asset_id", "")
            job_name = metadata.get("name", "unknown")
            # Scope the ID to avoid cross-project collisions
            scoped_id = f"{project_id}/{asset_id}"

            runs_url = f"{base}/v2/jobs/{asset_id}/runs"
            runs_params: dict[str, Any] = {"project_id": project_id, "limit": 5}

            try:
                runs_resp = await self.client.get(runs_url, headers=headers, params=runs_params)
                runs_resp.raise_for_status()
                runs: list[dict] = runs_resp.json().get("results", [])
            except httpx.HTTPStatusError as exc:
                self.logger.warning(
                    "Spark — failed runs for job=%s project=%s status=%s",
                    asset_id, project_id, exc.response.status_code,
                )
                runs = []
            except Exception as exc:
                self.logger.warning(
                    "Spark — error fetching runs job=%s project=%s error=%s",
                    asset_id, project_id, exc,
                )
                runs = []

            if runs:
                latest_run = runs[0]
                run_entity = latest_run.get("entity", {}).get("job_run", {})
                state = run_entity.get("state")
                started = self._parse_ts(run_entity.get("start_timestamp"))
                finished = self._parse_ts(run_entity.get("end_timestamp"))
                duration = run_entity.get("duration")
                run_id = latest_run.get("metadata", {}).get("asset_id", "")
            else:
                state, started, finished, duration, run_id = None, None, None, None, ""

            native_url = (
                f"{self.settings.CPD_BASE_URL}/projects/{project_id}/jobs/{asset_id}"
            )

            jobs.append(
                NormalizedJob(
                    component=ComponentType.SPARK,
                    job_id=scoped_id,
                    job_name=job_name,
                    status=self._map_state(state),
                    started_at=started,
                    finished_at=finished,
                    duration_seconds=float(duration) if duration is not None else None,
                    details={
                        "project_id": project_id,
                        "asset_id": asset_id,
                        "run_id": run_id,
                        "cpd_state": state,
                        "total_runs_fetched": len(runs),
                        "asset_ref_type": metadata.get("asset_ref_type", ""),
                    },
                    native_url=native_url,
                    last_polled_at=now,
                )
            )

        return jobs

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def get_health(self) -> ComponentHealth:
        """Compute health from the most recent cached Spark jobs.

        Returns
        -------
        ComponentHealth
            Aggregated status counts and reachability indicator.
        """
        cached = await self.get_cached(CACHE_KEY)
        if cached is not None:
            normalised = [NormalizedJob(**j) for j in cached]
            return compute_health(ComponentType.SPARK, normalised, is_reachable=True)

        # No cached data — try a fresh poll
        try:
            fresh = await self.poll()
            return compute_health(ComponentType.SPARK, fresh, is_reachable=True)
        except Exception as exc:
            self.logger.error("Spark health check failed — %s", exc)
            return compute_health(
                ComponentType.SPARK,
                [],
                is_reachable=False,
                error_message=str(exc),
            )
