using System.Text.Json.Serialization;

namespace IbmOpsHub.Models;

public class ComponentHealth
{
    public string Component { get; set; } = string.Empty;

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public ComponentStatus Status { get; set; } = ComponentStatus.Unknown;

    public int TotalJobs { get; set; }
    public int RunningJobs { get; set; }
    public int FailedJobs { get; set; }
    public int CompletedJobs { get; set; }
    public DateTime? LastPolled { get; set; }
    public string? ErrorMessage { get; set; }
}

public class DashboardSummary
{
    public int TotalJobs { get; set; }
    public int RunningJobs { get; set; }
    public int FailedJobs { get; set; }
    public int CompletedJobs { get; set; }
    public int HealthyComponents { get; set; }
    public int DegradedComponents { get; set; }
    public List<NormalizedJob> RecentFailures { get; set; } = [];
    public List<ComponentHealth> ComponentHealthList { get; set; } = [];
}
