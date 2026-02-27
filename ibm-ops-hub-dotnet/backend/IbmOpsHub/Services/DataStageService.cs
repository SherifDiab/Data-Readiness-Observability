using System.Net.Http.Headers;
using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

public class DataStageService(
    IHttpClientFactory httpFactory,
    AuthService auth,
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<DataStageService> logger) : IJobService
{
    private readonly AppSettings _s = settings.Value;
    public string Component => "datastage";

    public async Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default)
    {
        if (_s.MockMode) return MockData.DataStageJobs();

        var jobs = _s.DatastageUseCpd
            ? await PollCpdAsync(ct)
            : await PollIisAsync(ct);

        await cache.SetAsync("datastage:jobs", jobs, TimeSpan.FromSeconds(_s.DatastagePollInterval * 3));
        logger.LogInformation("DataStage: polled {Count} jobs", jobs.Count);
        return jobs;
    }

    public async Task<List<NormalizedJob>> GetCachedAsync()
        => await cache.GetAsync<List<NormalizedJob>>("datastage:jobs") ?? [];

    // ── CPD mode (DataStage as a service) ─────────────────────────────────────
    private async Task<List<NormalizedJob>> PollCpdAsync(CancellationToken ct)
    {
        var token = await auth.GetCpdTokenAsync(ct);
        var all = new List<NormalizedJob>();
        foreach (var projectId in _s.CpdProjectIdsList)
            all.AddRange(await PollCpdProjectAsync(projectId, token, ct));
        return all;
    }

    private async Task<List<NormalizedJob>> PollCpdProjectAsync(string projectId, string token, CancellationToken ct)
    {
        var jobs = new List<NormalizedJob>();
        try
        {
            var http = httpFactory.CreateClient("ibm");
            var req = new HttpRequestMessage(HttpMethod.Get,
                $"{_s.CpdBaseUrl}/v2/assets?project_id={projectId}&type_tag=datastage_flow&limit=200");
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
                            && ent.TryGetProperty("datastage_flow", out var ds)
                            && ds.TryGetProperty("last_run_status", out var st)
                    ? st.GetString() ?? "unknown" : "unknown";

                jobs.Add(new NormalizedJob
                {
                    Id = $"{projectId}/{assetId}",
                    Name = name,
                    Status = MapCpdState(state),
                    Component = "datastage",
                    LastPolled = now,
                    Details = new() { ["project_id"] = projectId, ["asset_id"] = assetId, ["raw_status"] = state }
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling DataStage CPD project {ProjectId}", projectId);
        }
        return jobs;
    }

    // ── IIS mode (legacy DataStage via ISF REST API) ──────────────────────────
    private async Task<List<NormalizedJob>> PollIisAsync(CancellationToken ct)
    {
        var jobs = new List<NormalizedJob>();
        try
        {
            var http = httpFactory.CreateClient("ibm");
            var req = new HttpRequestMessage(HttpMethod.Get, $"{_s.IisBaseUrl}/ibm/iis/ds/api/v1/jobs");
            req.Headers.Authorization = new AuthenticationHeaderValue("Basic", auth.GetIisBasicAuth());

            var resp = await http.SendAsync(req, ct);
            if (!resp.IsSuccessStatusCode) return jobs;

            using var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
            var now = DateTime.UtcNow;

            foreach (var job in doc.RootElement.EnumerateArray())
            {
                var jobId = job.TryGetProperty("Id", out var id) ? id.GetString() ?? "" : "";
                var name = job.TryGetProperty("Name", out var n) ? n.GetString() ?? "Unknown" : "Unknown";
                var statusCode = job.TryGetProperty("InvocationId", out var inv) &&
                                 inv.TryGetProperty("Status", out var sc) ? sc.GetInt32() : -1;

                DateTime? startedAt = null;
                if (job.TryGetProperty("InvocationId", out var inv2) &&
                    inv2.TryGetProperty("StartTime", out var st) &&
                    st.TryGetDateTimeOffset(out var dto))
                    startedAt = dto.UtcDateTime;

                jobs.Add(new NormalizedJob
                {
                    Id = jobId,
                    Name = name,
                    Status = MapIisState(statusCode),
                    Component = "datastage",
                    StartedAt = startedAt,
                    LastPolled = now,
                    Details = new() { ["iis_status_code"] = statusCode }
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling DataStage IIS");
        }
        return jobs;
    }

    private static JobStatus MapCpdState(string state) => state.ToLowerInvariant() switch
    {
        "completed" or "finished" => JobStatus.Completed,
        "running" => JobStatus.Running,
        "failed" => JobStatus.Failed,
        "queued" or "waiting" => JobStatus.Queued,
        "warning" => JobStatus.Warning,
        _ => JobStatus.Unknown
    };

    // IIS numeric status codes
    private static JobStatus MapIisState(int code) => code switch
    {
        0 => JobStatus.Running,
        1 => JobStatus.Completed,
        2 => JobStatus.Warning,
        3 => JobStatus.Failed,
        96 => JobStatus.Failed,
        97 => JobStatus.Canceled,
        _ => JobStatus.Unknown
    };
}
