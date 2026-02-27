using Microsoft.AspNetCore.SignalR;

namespace IbmOpsHub.Hubs;

/// <summary>
/// SignalR hub for real-time job updates.
/// Angular clients connect and receive "JobsUpdated" messages when polls complete.
/// </summary>
public class OpsHub : Hub
{
    /// <summary>Subscribe to updates for a specific component group.</summary>
    public async Task Subscribe(string component)
        => await Groups.AddToGroupAsync(Context.ConnectionId, component);

    /// <summary>Unsubscribe from a component group.</summary>
    public async Task Unsubscribe(string component)
        => await Groups.RemoveFromGroupAsync(Context.ConnectionId, component);

    public override async Task OnConnectedAsync()
    {
        // Auto-subscribe to "all" group
        await Groups.AddToGroupAsync(Context.ConnectionId, "all");
        await base.OnConnectedAsync();
    }
}
