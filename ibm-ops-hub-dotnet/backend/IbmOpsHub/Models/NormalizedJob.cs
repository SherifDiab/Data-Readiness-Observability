using System.Text.Json.Serialization;

namespace IbmOpsHub.Models;

public class NormalizedJob
{
    public string Id { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;

    [JsonConverter(typeof(JsonStringEnumConverter))]
    public JobStatus Status { get; set; } = JobStatus.Unknown;

    public string Component { get; set; } = string.Empty;
    public DateTime? StartedAt { get; set; }
    public DateTime? FinishedAt { get; set; }
    public double? DurationSeconds =>
        StartedAt.HasValue && FinishedAt.HasValue
            ? (FinishedAt.Value - StartedAt.Value).TotalSeconds
            : StartedAt.HasValue && Status == JobStatus.Running
                ? (DateTime.UtcNow - StartedAt.Value).TotalSeconds
                : null;
    public Dictionary<string, object?> Details { get; set; } = [];
    public DateTime LastPolled { get; set; } = DateTime.UtcNow;
}
