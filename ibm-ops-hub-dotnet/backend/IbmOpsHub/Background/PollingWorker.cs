using IbmOpsHub.Hubs;
using IbmOpsHub.Services.Interfaces;
using Microsoft.AspNetCore.SignalR;

namespace IbmOpsHub.Background;

/// <summary>
/// Generic background worker that polls an IJobService at a configurable interval
/// and broadcasts results to all SignalR clients.
/// </summary>
public abstract class PollingWorker<TService>(
    TService service,
    IHubContext<OpsHub> hub,
    ILogger logger) : BackgroundService
    where TService : IJobService
{
    protected abstract int PollIntervalSeconds { get; }

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        logger.LogInformation("Polling worker starting for component: {Component}", service.Component);

        // Initial poll shortly after startup
        await Task.Delay(TimeSpan.FromSeconds(5), ct);

        while (!ct.IsCancellationRequested)
        {
            try
            {
                var jobs = await service.PollAsync(ct);
                await hub.Clients.Group("all").SendAsync("JobsUpdated", new
                {
                    component = service.Component,
                    jobs,
                    timestamp = DateTime.UtcNow
                }, ct);
            }
            catch (OperationCanceledException)
            {
                break;
            }
            catch (Exception ex)
            {
                logger.LogError(ex, "Poll failed for component {Component}", service.Component);
            }

            try { await Task.Delay(TimeSpan.FromSeconds(PollIntervalSeconds), ct); }
            catch (OperationCanceledException) { break; }
        }

        logger.LogInformation("Polling worker stopped for component: {Component}", service.Component);
    }
}
