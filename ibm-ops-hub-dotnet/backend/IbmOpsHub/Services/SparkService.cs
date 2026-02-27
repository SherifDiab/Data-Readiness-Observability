using System.Net.Http.Headers;
using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

public class SparkService(
    IHttpClientFactory httpFactory,
    AuthService auth,
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<SparkService> logger) : IJobService
{
    private readonly AppSettings _s = settings.Value;
    public string Component => "spark";

    public async Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default)
    {
        if (_s.MockMode) return MockData.SparkJobs();

        var token = await auth.GetCpdTokenAsync(ct);
        var all = new List<NormalizedJob>();

        foreach (var projectId in _s.CpdProjectIdsList)
            all.AddRange(await PollProjectAsync(projectId, token, ct));

        await cache.SetAsync("spark:jobs", all, TimeSpan.FromSeconds(_s.SparkPollInterval * 3));
        logger.LogInformation("Spark: polled {Count} jobs across {N} projects", all.Count, _s.CpdProjectIdsList.Count);
        return all;
    }

    public async Task<List<NormalizedJob>> GetCachedAsync()
        => await cache.GetAsync<List<NormalizedJob>>("spark:jobs") ?? [];

    private async Task<List<NormalizedJob>> PollProjectAsync(string projectId, string token, CancellationToken ct)
    {
        var jobs = new List<NormalizedJob>();
        try
        {
            var http = httpFactory.CreateClient("ibm");
            var req = new HttpRequestMessage(HttpMethod.Get,
                $"{_s.CpdBaseUrl}/v2/assets?project_id={projectId}&type_tag=notebook&limit=200");
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            var resp = await http.SendAsync(req, ct);
            if (!resp.IsSuccessStatusCode) return jobs;

            using var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
            if (!doc.RootElement.TryGetProperty("results", out var results)) return jobs;

            var now = DateTime.UtcNow;
            foreach (var asset in results.EnumerateArray())
            {
                var meta = asset.GetProperty("metadata");
                var assetId = meta.GetProperty("asset_id").GetString() ?? "";
                var name = meta.GetProperty("name").GetString() ?? "Unknown";
                var state = asset.TryGetProperty("entity", out var ent)
                            && ent.TryGetProperty("notebook", out var nb)
                            && nb.TryGetProperty("last_job_status", out var st)
                    ? st.GetString() ?? "unknown" : "unknown";

                DateTime? startedAt = null;
                if (meta.TryGetProperty("create_time", out var ct2) && ct2.TryGetDateTimeOffset(out var dto))
                    startedAt = dto.UtcDateTime;

                jobs.Add(new NormalizedJob
                {
                    Id = $"{projectId}/{assetId}",
                    Name = name,
                    Status = MapState(state),
                    Component = "spark",
                    StartedAt = startedAt,
                    LastPolled = now,
                    Details = new() { ["project_id"] = projectId, ["asset_id"] = assetId, ["raw_status"] = state }
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling Spark project {ProjectId}", projectId);
        }
        return jobs;
    }

    private static JobStatus MapState(string state) => state.ToLowerInvariant() switch
    {
        "completed" or "finished" or "success" => JobStatus.Completed,
        "running" or "active" => JobStatus.Running,
        "failed" or "error" => JobStatus.Failed,
        "queued" or "waiting" or "starting" => JobStatus.Queued,
        _ => JobStatus.Unknown
    };
}
