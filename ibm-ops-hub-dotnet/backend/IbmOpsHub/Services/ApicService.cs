using System.Net.Http.Headers;
using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

public class ApicService(
    IHttpClientFactory httpFactory,
    AuthService auth,
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<ApicService> logger) : IJobService
{
    private readonly AppSettings _s = settings.Value;
    public string Component => "apic";

    public async Task<List<NormalizedJob>> PollAsync(CancellationToken ct = default)
    {
        // APIC service polls logs, not "jobs" in the same sense
        var logs = await FetchLogsAsync(ct);
        var summary = ComputeSummary(logs, "1h");
        await cache.SetAsync("apic:logs", logs, TimeSpan.FromSeconds(_s.ApicPollInterval * 3));
        await cache.SetAsync("apic:summary", summary, TimeSpan.FromSeconds(_s.ApicPollInterval * 3));
        logger.LogInformation("APIC: polled {Count} log entries", logs.Count);
        return []; // APIC doesn't produce NormalizedJob list; use GetLogsAsync/GetSummaryAsync instead
    }

    public async Task<List<NormalizedJob>> GetCachedAsync() => [];

    public async Task<List<ApiCallLog>> GetLogsAsync(string? apiName = null, string? statusCode = null)
    {
        var logs = await cache.GetAsync<List<ApiCallLog>>("apic:logs") ?? [];
        if (!string.IsNullOrEmpty(apiName))
            logs = logs.Where(l => l.ApiName.Contains(apiName, StringComparison.OrdinalIgnoreCase)).ToList();
        if (!string.IsNullOrEmpty(statusCode) && int.TryParse(statusCode, out var sc))
            logs = logs.Where(l => l.StatusCode == sc).ToList();
        return logs;
    }

    public async Task<ApicSummary> GetSummaryAsync(string timeframe = "1h")
    {
        var cached = await cache.GetAsync<ApicSummary>("apic:summary");
        return cached ?? new ApicSummary();
    }

    private async Task<List<ApiCallLog>> FetchLogsAsync(CancellationToken ct)
    {
        if (_s.MockMode) return MockData.ApicLogs();

        var logs = new List<ApiCallLog>();
        try
        {
            var token = await auth.GetApicTokenAsync(ct);
            var http = httpFactory.CreateClient("ibm");

            var since = DateTime.UtcNow.AddHours(-1).ToString("o");
            var req = new HttpRequestMessage(HttpMethod.Get,
                $"{_s.ApicAnalyticsUrl}/analytics/orgs/{_s.ApicOrg}/catalogs/{_s.ApicCatalog}/events?timerangestart={since}&limit=1000");
            req.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);

            var resp = await http.SendAsync(req, ct);
            if (!resp.IsSuccessStatusCode) return logs;

            using var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
            if (!doc.RootElement.TryGetProperty("events", out var events)) return logs;

            foreach (var ev in events.EnumerateArray())
            {
                DateTime ts = DateTime.UtcNow;
                if (ev.TryGetProperty("datetime", out var dt) && dt.TryGetDateTimeOffset(out var dto))
                    ts = dto.UtcDateTime;

                logs.Add(new ApiCallLog
                {
                    Timestamp = ts,
                    ApiName = ev.TryGetProperty("api_name", out var an) ? an.GetString() ?? "" : "",
                    Method = ev.TryGetProperty("request_verb", out var rv) ? rv.GetString() ?? "GET" : "GET",
                    Path = ev.TryGetProperty("resource_path", out var rp) ? rp.GetString() ?? "/" : "/",
                    StatusCode = ev.TryGetProperty("status_code", out var sc) ? sc.GetInt32() : 0,
                    LatencyMs = ev.TryGetProperty("time_to_serve_request", out var lat) ? lat.GetDouble() : 0,
                    OrgName = _s.ApicOrg,
                    CatalogName = _s.ApicCatalog,
                    ConsumerOrg = ev.TryGetProperty("consumer_org_name", out var co) ? co.GetString() ?? "" : "",
                    AppName = ev.TryGetProperty("app_name", out var ap) ? ap.GetString() ?? "" : ""
                });
            }
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Error polling APIC analytics");
        }
        return logs;
    }

    private static ApicSummary ComputeSummary(List<ApiCallLog> logs, string timeframe)
    {
        if (logs.Count == 0) return new ApicSummary { Timeframe = timeframe };

        var errors = logs.Where(l => l.StatusCode >= 400).ToList();
        var latencies = logs.Select(l => l.LatencyMs).OrderBy(x => x).ToList();
        var p95Idx = (int)Math.Ceiling(latencies.Count * 0.95) - 1;

        return new ApicSummary
        {
            Timeframe = timeframe,
            TotalCalls = logs.Count,
            ErrorCalls = errors.Count,
            ErrorRatePercent = logs.Count > 0 ? Math.Round(errors.Count * 100.0 / logs.Count, 2) : 0,
            AvgLatencyMs = Math.Round(logs.Average(l => l.LatencyMs), 2),
            P95LatencyMs = p95Idx >= 0 ? Math.Round(latencies[p95Idx], 2) : 0,
            TopErrors = errors
                .GroupBy(l => new { l.StatusCode, l.ApiName })
                .OrderByDescending(g => g.Count())
                .Take(10)
                .Select(g => new TopError { StatusCode = g.Key.StatusCode, ApiName = g.Key.ApiName, Count = g.Count() })
                .ToList(),
            CallsByMinute = logs
                .GroupBy(l => new DateTime(l.Timestamp.Year, l.Timestamp.Month, l.Timestamp.Day, l.Timestamp.Hour, l.Timestamp.Minute, 0))
                .OrderBy(g => g.Key)
                .Select(g => new CallsByMinute
                {
                    Minute = g.Key,
                    Calls = g.Count(),
                    Errors = g.Count(l => l.StatusCode >= 400)
                })
                .ToList()
        };
    }
}
