using System.Net.Http.Json;
using System.Text.Json;
using IbmOpsHub.Configuration;
using IbmOpsHub.Services.Interfaces;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Services;

/// <summary>Manages authentication tokens for CPD, IIS, and APIC. Tokens are cached in Redis.</summary>
public class AuthService(
    IHttpClientFactory httpFactory,
    ICacheService cache,
    IOptions<AppSettings> settings,
    ILogger<AuthService> logger)
{
    private readonly AppSettings _s = settings.Value;

    // ── CPD token ────────────────────────────────────────────────────────────
    public async Task<string> GetCpdTokenAsync(CancellationToken ct = default)
    {
        const string key = "auth:cpd_token";
        var cached = await cache.GetStringAsync(key);
        if (cached is not null) return cached;

        logger.LogInformation("Refreshing CPD auth token");
        var http = httpFactory.CreateClient("auth");
        var resp = await http.PostAsJsonAsync($"{_s.CpdBaseUrl}/icp4d-api/v1/authorize", new
        {
            username = _s.CpdUsername,
            password = _s.CpdPassword
        }, ct);

        resp.EnsureSuccessStatusCode();
        var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
        var token = doc.RootElement.GetProperty("token").GetString() ?? throw new InvalidOperationException("No token in CPD response");

        await cache.SetStringAsync(key, token, TimeSpan.FromMinutes(55));
        return token;
    }

    // ── APIC token ────────────────────────────────────────────────────────────
    public async Task<string> GetApicTokenAsync(CancellationToken ct = default)
    {
        const string key = "auth:apic_token";
        var cached = await cache.GetStringAsync(key);
        if (cached is not null) return cached;

        logger.LogInformation("Refreshing APIC auth token");
        var http = httpFactory.CreateClient("auth");
        var resp = await http.PostAsJsonAsync($"{_s.ApicMgmtUrl}/api/token", new
        {
            username = _s.ApicUsername,
            password = _s.ApicPassword,
            realm = _s.ApicRealm,
            client_id = "599b7aef-8841-4ee2-88a0-84d49c4d6ff2",
            client_secret = "0ea28423-e73b-47d4-b40e-ddb45c7eade9",
            grant_type = "password"
        }, ct);

        resp.EnsureSuccessStatusCode();
        var doc = await JsonDocument.ParseAsync(await resp.Content.ReadAsStreamAsync(ct), cancellationToken: ct);
        var token = doc.RootElement.GetProperty("access_token").GetString() ?? throw new InvalidOperationException("No token in APIC response");

        await cache.SetStringAsync(key, token, TimeSpan.FromMinutes(55));
        return token;
    }

    // ── IIS basic auth header ─────────────────────────────────────────────────
    public string GetIisBasicAuth()
    {
        var bytes = System.Text.Encoding.UTF8.GetBytes($"{_s.IisUsername}:{_s.IisPassword}");
        return Convert.ToBase64String(bytes);
    }

    public void InvalidateCpdToken() => _ = cache.DeleteAsync("auth:cpd_token");
    public void InvalidateApicToken() => _ = cache.DeleteAsync("auth:apic_token");
}
