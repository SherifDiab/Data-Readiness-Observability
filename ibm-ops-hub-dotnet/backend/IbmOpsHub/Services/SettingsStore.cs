using System.Reflection;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

/// <summary>
/// Redis-backed runtime settings store. Changes are persisted in Redis under
/// "settings:overrides" and applied to the live AppSettings singleton immediately.
/// </summary>
public class SettingsStore(
    ICacheService cache,
    IOptionsMonitor<AppSettings> monitor,
    ILogger<SettingsStore> logger)
{
    private const string RedisKey = "settings:overrides";
    private static readonly HashSet<string> SensitiveFields =
        ["CpdPassword", "IisPassword", "ApicPassword", "SlackWebhookUrl"];

    private static readonly Dictionary<string, List<SettingFieldDef>> Schema = new()
    {
        ["cpd"] =
        [
            new() { Key = "CpdBaseUrl", Label = "CPD Base URL", Type = "url", Required = true, Hint = "e.g. https://cpd.example.com" },
            new() { Key = "CpdUsername", Label = "CPD Username", Type = "text", Required = true },
            new() { Key = "CpdPassword", Label = "CPD Password", Type = "password", Sensitive = true, Required = true },
            new() { Key = "CpdProjectId", Label = "Default Project ID", Type = "text" },
            new() { Key = "CpdProjectIds", Label = "Project IDs (multi)", Type = "tags", Hint = "Comma-separated CP4D project IDs. Overrides Default Project ID when set." }
        ],
        ["datastage"] =
        [
            new() { Key = "DatastageUseCpd", Label = "Use CPD mode", Type = "boolean", Hint = "When enabled, DataStage is polled via CP4D. Disable to use the IIS REST API." },
            new() { Key = "IisBaseUrl", Label = "IIS Base URL", Type = "url" },
            new() { Key = "IisUsername", Label = "IIS Username", Type = "text" },
            new() { Key = "IisPassword", Label = "IIS Password", Type = "password", Sensitive = true }
        ],
        ["flink"] =
        [
            new() { Key = "FlinkRestUrl", Label = "Flink REST URL", Type = "url", Hint = "Primary Flink JobManager REST endpoint" },
            new() { Key = "FlinkClusters", Label = "Additional Clusters", Type = "tags", Hint = "Comma-separated extra Flink JobManager URLs" }
        ],
        ["event_processing"] =
        [
            new() { Key = "K8sNamespace", Label = "Kubernetes Namespace", Type = "text" },
            new() { Key = "K8sInCluster", Label = "In-cluster auth", Type = "boolean", Hint = "Enable when the app runs inside Kubernetes" },
            new() { Key = "K8sKubeconfig", Label = "Kubeconfig path", Type = "text", Hint = "Path to kubeconfig file (leave empty to use default)" },
            new() { Key = "FlinkCrdGroup", Label = "CRD API Group", Type = "text" },
            new() { Key = "FlinkCrdVersion", Label = "CRD API Version", Type = "text" }
        ],
        ["apic"] =
        [
            new() { Key = "ApicMgmtUrl", Label = "APIC Management URL", Type = "url" },
            new() { Key = "ApicAnalyticsUrl", Label = "APIC Analytics URL", Type = "url" },
            new() { Key = "ApicOrg", Label = "Organisation", Type = "text" },
            new() { Key = "ApicCatalog", Label = "Catalog", Type = "text" },
            new() { Key = "ApicUsername", Label = "Username", Type = "text" },
            new() { Key = "ApicPassword", Label = "Password", Type = "password", Sensitive = true },
            new() { Key = "ApicRealm", Label = "Realm", Type = "text" }
        ],
        ["polling"] =
        [
            new() { Key = "SparkPollInterval", Label = "Spark interval (s)", Type = "number", Min = 10, Max = 3600 },
            new() { Key = "DatastagePollInterval", Label = "DataStage interval (s)", Type = "number", Min = 10, Max = 3600 },
            new() { Key = "FlinkPollInterval", Label = "Flink interval (s)", Type = "number", Min = 5, Max = 3600 },
            new() { Key = "EventProcessingPollInterval", Label = "Event Processing interval (s)", Type = "number", Min = 10, Max = 3600 },
            new() { Key = "ApicPollInterval", Label = "APIC interval (s)", Type = "number", Min = 15, Max = 3600 }
        ],
        ["general"] =
        [
            new() { Key = "MockMode", Label = "Mock mode", Type = "boolean", Hint = "Return generated mock data instead of calling real IBM APIs" },
            new() { Key = "EnableAlerting", Label = "Enable alerting", Type = "boolean" },
            new() { Key = "SlackWebhookUrl", Label = "Slack Webhook URL", Type = "url", Sensitive = true }
        ]
    };

    public async Task<SettingsResponse> GetAllAsync()
    {
        var settings = monitor.CurrentValue;
        var overrides = (await cache.GetHashAsync(RedisKey)).Keys.ToList();
        var values = new Dictionary<string, object?>();

        foreach (var fields in Schema.Values)
        {
            foreach (var field in fields)
            {
                var prop = typeof(AppSettings).GetProperty(field.Key);
                var val = prop?.GetValue(settings);
                values[field.Key] = field.Sensitive
                    ? (val is string s && !string.IsNullOrEmpty(s) ? "••••••••" : null)
                    : val;
            }
        }

        return new SettingsResponse { Schema = Schema, Values = values, Overrides = overrides };
    }

    public async Task<SettingsUpdateResult> UpdateAsync(Dictionary<string, object?> changes)
    {
        var applied = new List<string>();
        var skipped = new List<string>();
        var settings = monitor.CurrentValue;
        var stored = await cache.GetHashAsync(RedisKey);

        foreach (var (key, rawValue) in changes)
        {
            var prop = typeof(AppSettings).GetProperty(key);
            if (prop is null) { skipped.Add(key); continue; }

            // Sensitive: skip placeholder
            if (SensitiveFields.Contains(key) && rawValue?.ToString() is "••••••••") { skipped.Add(key); continue; }

            try
            {
                var converted = Convert.ChangeType(rawValue, prop.PropertyType);
                prop.SetValue(settings, converted);
                stored[key] = rawValue?.ToString() ?? "";
                applied.Add(key);
                logger.LogInformation("Applied setting {Key}", key);
            }
            catch (Exception ex)
            {
                logger.LogWarning(ex, "Failed to apply setting {Key}", key);
                skipped.Add(key);
            }
        }

        if (applied.Count > 0)
            await cache.SetHashAsync(RedisKey, stored);

        return new SettingsUpdateResult { Applied = applied, Skipped = skipped };
    }

    public async Task LoadOverridesOnStartupAsync()
    {
        var stored = await cache.GetHashAsync(RedisKey);
        if (stored.Count == 0) return;

        var fakeChanges = stored.ToDictionary(kv => kv.Key, kv => (object?)kv.Value);
        var result = await UpdateAsync(fakeChanges);
        logger.LogInformation("Restored {Count} setting overrides from Redis", result.Applied.Count);
    }
}
