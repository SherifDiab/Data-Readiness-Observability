"""
Application configuration loaded from environment variables via Pydantic Settings.
All IBM service credentials, polling intervals, and feature flags are centralized here.
Settings can also be overridden at runtime via the /api/settings endpoint (persisted in Redis).
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Cloud Pak for Data (Spark + DataStage)
    CPD_BASE_URL: str = "https://cpd-instance.example.com"
    CPD_USERNAME: str = "admin"
    CPD_PASSWORD: str = "changeme"
    # Single project (legacy). If CPD_PROJECT_IDS is set, it takes precedence.
    CPD_PROJECT_ID: str = "default-project"
    # Comma-separated list of CPD project IDs to monitor across ALL Spark + DataStage jobs.
    # Example: "proj-analytics,proj-finance,proj-ops"
    # Leave empty to fall back to CPD_PROJECT_ID.
    CPD_PROJECT_IDS: str = ""

    @property
    def cpd_project_ids_list(self) -> list[str]:
        """Return the effective list of CPD project IDs to monitor."""
        if self.CPD_PROJECT_IDS.strip():
            return [p.strip() for p in self.CPD_PROJECT_IDS.split(",") if p.strip()]
        return [self.CPD_PROJECT_ID]

    # DataStage (same CPD instance or separate IIS)
    DATASTAGE_USE_CPD: bool = True
    IIS_BASE_URL: str = ""
    IIS_USERNAME: str = ""
    IIS_PASSWORD: str = ""

    # Kubernetes (for Event Processing FlinkDeployments)
    K8S_IN_CLUSTER: bool = True
    K8S_KUBECONFIG: str = ""
    K8S_NAMESPACE: str = "event-automation"
    FLINK_CRD_GROUP: str = "flink.apache.org"
    FLINK_CRD_VERSION: str = "v1beta1"

    # Flink REST API (standalone / custom jobs)
    FLINK_REST_URL: str = "http://flink-jobmanager:8081"
    FLINK_CLUSTERS: str = ""

    # API Connect
    APIC_MGMT_URL: str = "https://apic-mgmt.example.com"
    APIC_ANALYTICS_URL: str = "https://apic-analytics.example.com"
    APIC_ORG: str = "myorg"
    APIC_CATALOG: str = "sandbox"
    APIC_USERNAME: str = "admin"
    APIC_PASSWORD: str = "changeme"
    APIC_REALM: str = "provider/default-idp-2"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # PostgreSQL
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/opshub"

    # Polling intervals (seconds)
    SPARK_POLL_INTERVAL: int = 30
    DATASTAGE_POLL_INTERVAL: int = 30
    FLINK_POLL_INTERVAL: int = 15
    EVENT_PROCESSING_POLL_INTERVAL: int = 30
    APIC_POLL_INTERVAL: int = 60

    # Feature flags
    MOCK_MODE: bool = False
    MOCK_SERVER_URL: str = "http://mock-server:9000"
    ENABLE_ALERTING: bool = False
    SLACK_WEBHOOK_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
