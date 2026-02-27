using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/datastage")]
public class DataStageController(DataStageService datastage) : ControllerBase
{
    [HttpGet("jobs")]
    public async Task<IActionResult> GetJobs() => Ok(await datastage.GetCachedAsync());

    [HttpPost("poll")]
    public async Task<IActionResult> ForcePoll(CancellationToken ct)
    {
        var jobs = await datastage.PollAsync(ct);
        return Ok(new { count = jobs.Count, jobs });
    }
}
