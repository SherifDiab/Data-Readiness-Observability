using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/flink")]
public class FlinkController(FlinkService flink) : ControllerBase
{
    [HttpGet("jobs")]
    public async Task<IActionResult> GetJobs() => Ok(await flink.GetCachedAsync());

    [HttpPost("poll")]
    public async Task<IActionResult> ForcePoll(CancellationToken ct)
    {
        var jobs = await flink.PollAsync(ct);
        return Ok(new { count = jobs.Count, jobs });
    }
}
