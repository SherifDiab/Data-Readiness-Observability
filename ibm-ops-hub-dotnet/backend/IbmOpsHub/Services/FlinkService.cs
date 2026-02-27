using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

public class FlinkService(
    IHttpClientFactory httpFactory,
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<FlinkService> logger) : IJobService
{
    private readonly AppSettings _s = settings.Value;
    public string Component => "flink";

    public async Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default)
    {
        if (_s.MockMode) return MockData.FlinkJobs();

        var clusterUrls = string.IsNullOrWhiteSpace(_s.FlinkClusters)
            ? [_s.FlinkRestUrl]
            : _s.FlinkClusters.Split(',').Select(u => u.Trim()).Where(u => !string.IsNullOrEmpty(u)).ToList();

        var all = new List<NormalizedJob>();
        foreach (var url in clusterUrls)
            all.AddRange(await PollClusterAsync(url, ct));

        await cache.SetAsync("flink:jobs", all, TimeSpan.FromSeconds(_s.FlinkPollInterval * 3));
        logger.LogInformation("Flink: polled {Count} jobs", all.Count);
        return all;
    }

    public async Task<List<NormalizedJob>> GetCachedAsync()
        => await cache.GetAsync<List<NormalizedJob>>("flink:jobs") ?? [];

    private async Task<List<NormalizedJob>> PollClusterAsync(string baseUrl, CancellationToken ct)
    {
        var jobs = new List<NormalizedJob>();
        if (string.IsNullOrWhiteSpace(baseUrl)) return jobs;

        try
        {
            var http = httpFactory.CreateClient("ibm");
            var resp = await http.GetAsync($"{baseUrl}/jobs/overview", ct);
            if (!resp.IsSuccessStatusCode) return jobs;

            using var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
            if (!doc.RootElement.TryGetProperty("jobs", out var jobsArr)) return jobs;

            foreach (var job in jobsArr.EnumerateArray())
            {
                var jobId = job.GetProperty("jid").GetString() ?? "";
                var name = job.TryGetProperty("name", out var n) ? n.GetString() ?? "Unknown" : "Unknown";
                var state = job.TryGetProperty("state", out var s) ? s.GetString() ?? "UNKNOWN" : "UNKNOWN";

                DateTime? startedAt = null;
                if (job.TryGetProperty("start-time", out var st) && st.TryGetInt64(out var ms) && ms > 0)
                    startedAt = DateTimeOffset.FromUnixTimeMilliseconds(ms).UtcDateTime;

                DateTime? finishedAt = null;
                if (job.TryGetProperty("end-time", out var et) && et.TryGetInt64(out var ems) && ems > 0)
                    finishedAt = DateTimeOffset.FromUnixTimeMilliseconds(ems).UtcDateTime;

                jobs.Add(new NormalizedJob
                {
                    Id = jobId,
                    Name = name,
                    Status = MapFlinkState(state),
                    Component = "flink",
                    StartedAt = startedAt,
                    FinishedAt = finishedAt,
                    LastPolled = DateTime.UtcNow,
                    Details = new() { ["cluster_url"] = baseUrl, ["raw_state"] = state }
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling Flink cluster {Url}", baseUrl);
        }
        return jobs;
    }

    private static JobStatus MapFlinkState(string state) => state.ToUpperInvariant() switch
    {
        "RUNNING" => JobStatus.Running,
        "FINISHED" => JobStatus.Completed,
        "FAILED" => JobStatus.Failed,
        "CANCELED" or "CANCELLING" => JobStatus.Canceled,
        "CREATED" or "INITIALIZING" => JobStatus.Queued,
        "RESTARTING" => JobStatus.Restarting,
        "SUSPENDED" => JobStatus.Suspended,
        _ => JobStatus.Unknown
    };
}
