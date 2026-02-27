"""
DataStage service poller for IBM Cloud Pak for Data / Information Server.

Supports two connectivity modes controlled by ``DATASTAGE_USE_CPD``:

1. **CPD mode** (default) — uses the same CPD v2 Jobs API as Spark but filters
   for jobs whose ``asset_ref_type == "data_intg_flow"`` (DataStage flows).
2. **IIS mode** — uses the legacy Information Server REST API at
   ``{IIS_BASE_URL}/ibm/iis/api/...`` with basic auth.

In both cases the results are normalised into ``NormalizedJob`` with extra
detail fields for ``rows_read`` and ``rows_written``.

CPD API reference (DataStage flows)
------------------------------------
List jobs (filtered):
    GET {CPD_BASE_URL}/v2/jobs?project_id={pid}&limit=100
    Filter for entries where metadata.asset_ref_type == "data_intg_flow"

List runs:
    GET {CPD_BASE_URL}/v2/jobs/{job_id}/runs?project_id={pid}&limit=5
    Response entity.job_run contains state, start/end timestamps, and
    optional counters (rows_read, rows_written) when available.

IIS API reference
-----------------
List DataStage jobs:
    GET {IIS_BASE_URL}/ibm/iis/api/datastage/flows
    Authorization: Basic <base64>
    Response:
    {
        "flows": [
            {
                "id": "...",
                "name": "...",
                "last_run": {
                    "status": "finished|failed|running|...",
                    "started_at": "...",
                    "ended_at": "...",
                    "rows_read": 50000,
                    "rows_written": 49800
                }
            }
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

# CPD state -> JobStatus (same mapping as Spark)
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

# IIS state -> JobStatus
_IIS_STATE_MAP: dict[str, JobStatus] = {
    "finished": JobStatus.COMPLETED,
    "running": JobStatus.RUNNING,
    "failed": JobStatus.FAILED,
    "cancelled": JobStatus.CANCELED,
    "waiting": JobStatus.QUEUED,
    "warning": JobStatus.WARNING,
}

CACHE_KEY = "datastage:jobs"


class DataStageService(BaseService):
    """Polls IBM DataStage job/flow statuses via CPD or IIS APIs.

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

    def _cpd_base_url(self) -> str:
        """Return the CPD base URL, switching to mock server when enabled."""
        if self.settings.MOCK_MODE:
            return self.settings.MOCK_SERVER_URL
        return self.settings.CPD_BASE_URL

    def _iis_base_url(self) -> str:
        """Return the IIS base URL, switching to mock server when enabled."""
        if self.settings.MOCK_MODE:
            return self.settings.MOCK_SERVER_URL
        return self.settings.IIS_BASE_URL

    @staticmethod
    def _map_cpd_state(cpd_state: str | None) -> JobStatus:
        if cpd_state is None:
            return JobStatus.UNKNOWN
        return _CPD_STATE_MAP.get(cpd_state, JobStatus.UNKNOWN)

    @staticmethod
    def _map_iis_state(iis_state: str | None) -> JobStatus:
        if iis_state is None:
            return JobStatus.UNKNOWN
        return _IIS_STATE_MAP.get(iis_state.lower(), JobStatus.UNKNOWN)

    @staticmethod
    def _parse_ts(ts_str: str | None) -> datetime | None:
        if not ts_str:
            return None
        try:
            return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # CPD-mode polling
    # ------------------------------------------------------------------

    async def _poll_cpd(self) -> list[NormalizedJob]:
        """Poll DataStage flows via the CPD v2 Jobs API across all configured projects.

        Iterates over every project in ``settings.cpd_project_ids_list`` and
        filters the jobs list for entries with ``asset_ref_type == "data_intg_flow"``.
        Job IDs are scoped as ``{project_id}/{asset_id}`` to prevent collisions.

        Returns
        -------
        list[NormalizedJob]
            DataStage jobs normalised with rows_read / rows_written details.
        """
        base = self._cpd_base_url()
        all_jobs: list[NormalizedJob] = []

        token = await self.auth_service.get_cpd_token()
        headers = {"Authorization": f"Bearer {token}"}
        project_ids = self.settings.cpd_project_ids_list

        self.logger.info(
            "DataStage (CPD) poll — monitoring %d project(s): %s",
            len(project_ids), project_ids,
        )

        for project_id in project_ids:
            try:
                project_jobs = await self._poll_cpd_project(base, project_id, headers)
                all_jobs.extend(project_jobs)
                self.logger.info(
                    "DataStage (CPD) — project=%s yielded %d flows",
                    project_id, len(project_jobs),
                )
            except Exception as exc:
                self.logger.error(
                    "DataStage (CPD) — project=%s failed: %s", project_id, exc
                )

        return all_jobs

    async def _poll_cpd_project(
        self,
        base: str,
        project_id: str,
        headers: dict[str, str],
    ) -> list[NormalizedJob]:
        """Poll a single CPD project for DataStage flow jobs."""
        now = datetime.now(timezone.utc)
        jobs: list[NormalizedJob] = []

        jobs_url = f"{base}/v2/jobs"
        params: dict[str, Any] = {"project_id": project_id, "limit": 100}

        self.logger.info("DataStage (CPD) — GET %s project=%s", jobs_url, project_id)
        resp = await self.client.get(jobs_url, headers=headers, params=params)
        resp.raise_for_status()
        all_results: list[dict] = resp.json().get("results", [])

        # Filter for DataStage integration flows
        ds_jobs = [
            j for j in all_results
            if j.get("metadata", {}).get("asset_ref_type") == "data_intg_flow"
        ]
        self.logger.info(
            "DataStage (CPD) — %d DataStage flows out of %d total jobs in project=%s",
            len(ds_jobs), len(all_results), project_id,
        )

        for job_entry in ds_jobs:
            metadata = job_entry.get("metadata", {})
            asset_id = metadata.get("asset_id", "")
            job_name = metadata.get("name", "unknown")
            scoped_id = f"{project_id}/{asset_id}"

            runs_url = f"{base}/v2/jobs/{asset_id}/runs"
            runs_params: dict[str, Any] = {"project_id": project_id, "limit": 5}

            try:
                runs_resp = await self.client.get(runs_url, headers=headers, params=runs_params)
                runs_resp.raise_for_status()
                runs: list[dict] = runs_resp.json().get("results", [])
            except httpx.HTTPStatusError as exc:
                self.logger.warning(
                    "DataStage (CPD) — failed runs for job=%s project=%s status=%s",
                    asset_id, project_id, exc.response.status_code,
                )
                runs = []
            except Exception as exc:
                self.logger.warning(
                    "DataStage (CPD) — error fetching runs job=%s project=%s error=%s",
                    asset_id, project_id, exc,
                )
                runs = []

            if runs:
                latest = runs[0]
                run_entity = latest.get("entity", {}).get("job_run", {})
                state = run_entity.get("state")
                started = self._parse_ts(run_entity.get("start_timestamp"))
                finished = self._parse_ts(run_entity.get("end_timestamp"))
                duration = run_entity.get("duration")
                rows_read = run_entity.get("rows_read", 0)
                rows_written = run_entity.get("rows_written", 0)
                run_id = latest.get("metadata", {}).get("asset_id", "")
            else:
                state, started, finished, duration = None, None, None, None
                rows_read, rows_written, run_id = 0, 0, ""

            native_url = f"{self.settings.CPD_BASE_URL}/projects/{project_id}/jobs/{asset_id}"

            jobs.append(
                NormalizedJob(
                    component=ComponentType.DATASTAGE,
                    job_id=scoped_id,
                    job_name=job_name,
                    status=self._map_cpd_state(state),
                    started_at=started,
                    finished_at=finished,
                    duration_seconds=float(duration) if duration is not None else None,
                    details={
                        "project_id": project_id,
                        "asset_id": asset_id,
                        "run_id": run_id,
                        "cpd_state": state,
                        "rows_read": rows_read,
                        "rows_written": rows_written,
                        "mode": "cpd",
                    },
                    native_url=native_url,
                    last_polled_at=now,
                )
            )

        return jobs

    # ------------------------------------------------------------------
    # IIS-mode polling
    # ------------------------------------------------------------------

    async def _poll_iis(self) -> list[NormalizedJob]:
        """Poll DataStage flows via the legacy IIS REST API.

        Returns
        -------
        list[NormalizedJob]
            DataStage jobs normalised with rows_read / rows_written details.
        """
        now = datetime.now(timezone.utc)
        base = self._iis_base_url()
        jobs: list[NormalizedJob] = []

        url = f"{base}/ibm/iis/api/datastage/flows"
        auth = (self.settings.IIS_USERNAME, self.settings.IIS_PASSWORD)

        self.logger.info("DataStage (IIS) poll — GET %s", url)
        resp = await self.client.get(url, auth=auth)
        resp.raise_for_status()
        flows: list[dict] = resp.json().get("flows", [])

        for flow in flows:
            flow_id = flow.get("id", "")
            flow_name = flow.get("name", "unknown")
            last_run = flow.get("last_run", {})

            state = last_run.get("status")
            started = self._parse_ts(last_run.get("started_at"))
            finished = self._parse_ts(last_run.get("ended_at"))
            rows_read = last_run.get("rows_read", 0)
            rows_written = last_run.get("rows_written", 0)

            duration = None
            if started and finished:
                duration = (finished - started).total_seconds()

            jobs.append(
                NormalizedJob(
                    component=ComponentType.DATASTAGE,
                    job_id=flow_id,
                    job_name=flow_name,
                    status=self._map_iis_state(state),
                    started_at=started,
                    finished_at=finished,
                    duration_seconds=duration,
                    details={
                        "iis_state": state,
                        "rows_read": rows_read,
                        "rows_written": rows_written,
                        "mode": "iis",
                    },
                    native_url=f"{self.settings.IIS_BASE_URL}/datastage/flows/{flow_id}",
                    last_polled_at=now,
                )
            )

        return jobs

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def poll(self) -> list[NormalizedJob]:
        """Fetch DataStage jobs using the configured mode (CPD or IIS).

        The mode is determined by ``settings.DATASTAGE_USE_CPD``.

        Returns
        -------
        list[NormalizedJob]
            Normalised DataStage jobs.
        """
        jobs: list[NormalizedJob] = []
        try:
            if self.settings.DATASTAGE_USE_CPD:
                jobs = await self._poll_cpd()
            else:
                jobs = await self._poll_iis()

            await self.cache_results(
                CACHE_KEY, jobs, ttl=self.settings.DATASTAGE_POLL_INTERVAL * 4
            )
            self.logger.info("DataStage poll complete — %d jobs normalised", len(jobs))

        except httpx.HTTPStatusError as exc:
            self.logger.error(
                "DataStage poll failed — endpoint=%s status=%s body=%s",
                exc.request.url,
                exc.response.status_code,
                exc.response.text[:500],
            )
        except Exception as exc:
            self.logger.error("DataStage poll error — %s", exc, exc_info=True)

        return jobs

    async def get_health(self) -> ComponentHealth:
        """Compute health from the most recent cached DataStage jobs.

        Returns
        -------
        ComponentHealth
            Aggregated status counts and reachability indicator.
        """
        cached = await self.get_cached(CACHE_KEY)
        if cached is not None:
            normalised = [NormalizedJob(**j) for j in cached]
            return compute_health(ComponentType.DATASTAGE, normalised, is_reachable=True)

        try:
            fresh = await self.poll()
            return compute_health(ComponentType.DATASTAGE, fresh, is_reachable=True)
        except Exception as exc:
            self.logger.error("DataStage health check failed — %s", exc)
            return compute_health(
                ComponentType.DATASTAGE,
                [],
                is_reachable=False,
                error_message=str(exc),
            )
