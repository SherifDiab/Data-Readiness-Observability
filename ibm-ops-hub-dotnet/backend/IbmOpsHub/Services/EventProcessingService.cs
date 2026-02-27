using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using k8s;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

public class EventProcessingService(
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<EventProcessingService> logger) : IJobService
{
    private readonly AppSettings _s = settings.Value;
    public string Component => "event_processing";

    public async Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default)
    {
        if (_s.MockMode) return MockData.EventProcessingFlows();

        var flows = await PollK8sAsync(ct);
        await cache.SetAsync("event_processing:flows", flows, TimeSpan.FromSeconds(_s.EventProcessingPollInterval * 3));
        logger.LogInformation("EventProcessing: polled {Count} flows", flows.Count);
        return flows;
    }

    public async Task<List<NormalizedJob>> GetCachedAsync()
        => await cache.GetAsync<List<NormalizedJob>>("event_processing:flows") ?? [];

    private async Task<List<NormalizedJob>> PollK8sAsync(CancellationToken ct)
    {
        var flows = new List<NormalizedJob>();
        try
        {
            var config = _s.K8sInCluster
                ? KubernetesClientConfiguration.InClusterConfig()
                : string.IsNullOrEmpty(_s.K8sKubeconfig)
                    ? KubernetesClientConfiguration.BuildConfigFromConfigFile()
                    : KubernetesClientConfiguration.BuildConfigFromConfigFile(_s.K8sKubeconfig);

            var client = new Kubernetes(config);
            var group = _s.FlinkCrdGroup;
            var version = _s.FlinkCrdVersion;
            var ns = _s.K8sNamespace;

            var crdList = await client.CustomObjects.ListNamespacedCustomObjectAsync(
                group, version, ns, "flinkdeployments", cancellationToken: ct);

            var json = JsonSerializer.Serialize(crdList);
            using var doc = JsonDocument.Parse(json);

            if (!doc.RootElement.TryGetProperty("items", out var items)) return flows;

            var now = DateTime.UtcNow;
            foreach (var item in items.EnumerateArray())
            {
                var name = item.GetProperty("metadata").GetProperty("name").GetString() ?? "Unknown";
                var ns2 = item.GetProperty("metadata").TryGetProperty("namespace", out var nsEl)
                    ? nsEl.GetString() ?? ns : ns;
                var state = item.TryGetProperty("status", out var status) &&
                            status.TryGetProperty("lifecycleState", out var ls)
                    ? ls.GetString() ?? "UNKNOWN" : "UNKNOWN";
                var jobState = item.TryGetProperty("status", out var st2) &&
                               st2.TryGetProperty("jobStatus", out var js) &&
                               js.TryGetProperty("state", out var jss)
                    ? jss.GetString() ?? "" : "";

                flows.Add(new NormalizedJob
                {
                    Id = $"{ns2}/{name}",
                    Name = name,
                    Status = MapK8sState(state, jobState),
                    Component = "event_processing",
                    LastPolled = now,
                    Details = new() { ["namespace"] = ns2, ["lifecycle_state"] = state, ["job_state"] = jobState }
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling K8s FlinkDeployments");
        }
        return flows;
    }

    private static JobStatus MapK8sState(string lifecycle, string jobState) =>
        lifecycle.ToUpperInvariant() switch
        {
            "RUNNING" => jobState.Equals("RUNNING", StringComparison.OrdinalIgnoreCase)
                ? JobStatus.Running : JobStatus.Restarting,
            "READY" => JobStatus.Running,
            "FINISHED" or "COMPLETED" => JobStatus.Completed,
            "FAILED" => JobStatus.Failed,
            "CANCELED" or "CANCELLING" => JobStatus.Canceled,
            "SUSPENDED" => JobStatus.Suspended,
            "RECONCILING" or "DEPLOYING" => JobStatus.Restarting,
            _ => JobStatus.Unknown
        };
}
