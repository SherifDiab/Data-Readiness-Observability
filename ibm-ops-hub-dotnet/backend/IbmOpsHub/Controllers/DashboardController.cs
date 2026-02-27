using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/dashboard")]
public class DashboardController(DashboardService dashboard) : ControllerBase
{
    [HttpGet("summary")]
    public async Task<IActionResult> GetSummary() => Ok(await dashboard.GetSummaryAsync());

    [HttpGet("health")]
    public async Task<IActionResult> GetHealth() => Ok(await dashboard.GetHealthAsync());
}
