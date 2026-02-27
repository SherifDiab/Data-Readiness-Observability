using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/apic")]
public class ApicController(ApicService apic) : ControllerBase
{
    [HttpGet("logs")]
    public async Task<IActionResult> GetLogs([FromQuery] string? apiName, [FromQuery] string? statusCode)
        => Ok(await apic.GetLogsAsync(apiName, statusCode));

    [HttpGet("summary")]
    public async Task<IActionResult> GetSummary([FromQuery] string timeframe = "1h")
        => Ok(await apic.GetSummaryAsync(timeframe));

    [HttpPost("poll")]
    public async Task<IActionResult> ForcePoll(CancellationToken ct)
    {
        await apic.PollAsync(ct);
        return Ok(new { status = "triggered" });
    }
}
