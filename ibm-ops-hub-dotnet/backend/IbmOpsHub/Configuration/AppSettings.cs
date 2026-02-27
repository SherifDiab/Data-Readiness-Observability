namespace IbmOpsHub.Configuration;

public class AppSettings
{
    // ── Cloud Pak for Data ────────────────────────────────────────────────────
    public string CpdBaseUrl { get; set; } = string.Empty;
    public string CpdUsername { get; set; } = string.Empty;
    public string CpdPassword { get; set; } = string.Empty;
    public string CpdProjectId { get; set; } = "default-project";
    /// <summary>Comma-separated list of CP4D project IDs (overrides CpdProjectId).</summary>
    public string CpdProjectIds { get; set; } = string.Empty;

    public List<string> CpdProjectIdsList =>
        !string.IsNullOrWhiteSpace(CpdProjectIds)
            ? CpdProjectIds.Split(',').Select(p => p.Trim()).Where(p => !string.IsNullOrEmpty(p)).ToList()
            : [CpdProjectId];

    // ── DataStage ─────────────────────────────────────────────────────────────
    public bool DatastageUseCpd { get; set; } = true;
    public string IisBaseUrl { get; set; } = string.Empty;
    public string IisUsername { get; set; } = string.Empty;
    public string IisPassword { get; set; } = string.Empty;

    // ── Kubernetes / Event Processing ─────────────────────────────────────────
    public bool K8sInCluster { get; set; } = false;
    public string K8sKubeconfig { get; set; } = string.Empty;
    public string K8sNamespace { get; set; } = "event-automation";
    public string FlinkCrdGroup { get; set; } = "flink.apache.org";
    public string FlinkCrdVersion { get; set; } = "v1beta1";

    // ── Flink REST ────────────────────────────────────────────────────────────
    public string FlinkRestUrl { get; set; } = string.Empty;
    public string FlinkClusters { get; set; } = string.Empty;

    // ── API Connect ───────────────────────────────────────────────────────────
    public string ApicMgmtUrl { get; set; } = string.Empty;
    public string ApicAnalyticsUrl { get; set; } = string.Empty;
    public string ApicOrg { get; set; } = string.Empty;
    public string ApicCatalog { get; set; } = string.Empty;
    public string ApicUsername { get; set; } = string.Empty;
    public string ApicPassword { get; set; } = string.Empty;
    public string ApicRealm { get; set; } = "provider/default-idp-2";

    // ── Polling intervals (seconds) ───────────────────────────────────────────
    public int SparkPollInterval { get; set; } = 30;
    public int DatastagePollInterval { get; set; } = 30;
    public int FlinkPollInterval { get; set; } = 15;
    public int EventProcessingPollInterval { get; set; } = 30;
    public int ApicPollInterval { get; set; } = 60;

    // ── Feature flags ─────────────────────────────────────────────────────────
    public bool MockMode { get; set; } = false;
    public string MockServerUrl { get; set; } = "http://localhost:9000";
    public bool EnableAlerting { get; set; } = false;
    public string SlackWebhookUrl { get; set; } = string.Empty;
}
