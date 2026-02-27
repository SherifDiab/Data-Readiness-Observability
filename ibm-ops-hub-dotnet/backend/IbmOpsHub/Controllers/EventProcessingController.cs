using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/event-processing")]
public class EventProcessingController(EventProcessingService ep) : ControllerBase
{
    [HttpGet("flows")]
    public async Task<IActionResult> GetFlows() => Ok(await ep.GetCachedAsync());

    [HttpPost("poll")]
    public async Task<IActionResult> ForcePoll(CancellationToken ct)
    {
        var flows = await ep.PollAsync(ct);
        return Ok(new { count = flows.Count, flows });
    }
}
