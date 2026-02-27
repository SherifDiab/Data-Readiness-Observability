using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/spark")]
public class SparkController(SparkService spark) : ControllerBase
{
    [HttpGet("jobs")]
    public async Task<IActionResult> GetJobs() => Ok(await spark.GetCachedAsync());

    [HttpPost("poll")]
    public async Task<IActionResult> ForcePoll(CancellationToken ct)
    {
        var jobs = await spark.PollAsync(ct);
        return Ok(new { count = jobs.Count, jobs });
    }
}
