using IbmOpsHub.Models;
using IbmOpsHub.Services;
using Microsoft.AspNetCore.Mvc;

namespace IbmOpsHub.Controllers;

[ApiController]
[Route("api/settings")]
public class SettingsController(SettingsStore store) : ControllerBase
{
    [HttpGet]
    public async Task<IActionResult> Get() => Ok(await store.GetAllAsync());

    [HttpGet("schema")]
    public async Task<IActionResult> GetSchema()
    {
        var data = await store.GetAllAsync();
        return Ok(new { schema = data.Schema });
    }

    [HttpPut]
    public async Task<IActionResult> Update([FromBody] SettingsUpdateRequest request)
    {
        var result = await store.UpdateAsync(request.Changes);
        return Ok(result);
    }

    [HttpPost("refresh/{component}")]
    public IActionResult Refresh(string component)
    {
        var valid = new[] { "spark", "datastage", "flink", "event_processing", "apic" };
        if (!valid.Contains(component))
            return BadRequest(new { error = $"Invalid component. Must be one of: {string.Join(", ", valid)}" });

        // The background workers will pick up settings changes on next cycle.
        // Returning 202 Accepted is appropriate here.
        return Accepted(new { status = "accepted", component, message = "Next poll will use updated settings." });
    }
}
