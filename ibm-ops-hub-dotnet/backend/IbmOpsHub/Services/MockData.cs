using IbmOpsHub.Models;

namespace IbmOpsHub.Services;

/// <summary>Generates realistic mock data when MockMode = true.</summary>
public static class MockData
{
    private static readonly Random Rng = new();
    private static readonly string[] SparkStates = ["Completed", "Running", "Failed", "Queued"];
    private static readonly string[] DataStageStates = ["Completed", "Running", "Failed", "Warning"];
    private static readonly string[] FlinkStates = ["RUNNING", "FINISHED", "FAILED", "CANCELED"];
    private static readonly string[] K8sStates = ["RUNNING", "FINISHED", "FAILED", "SUSPENDED"];

    private static JobStatus Rand(string[] states)
    {
        var s = states[Rng.Next(states.Length)];
        return s switch
        {
            "Running" or "RUNNING" => JobStatus.Running,
            "Completed" or "FINISHED" => JobStatus.Completed,
            "Failed" or "FAILED" => JobStatus.Failed,
            "Warning" => JobStatus.Warning,
            "Queued" or "CANCELED" => JobStatus.Queued,
            "SUSPENDED" => JobStatus.Suspended,
            _ => JobStatus.Unknown
        };
    }

    public static List<NormalizedJob> SparkJobs() =>
        Enumerable.Range(1, 8).Select(i => new NormalizedJob
        {
            Id = $"proj-{(i % 2) + 1}/spark-asset-{i}",
            Name = $"Spark Notebook {i}",
            Status = Rand(SparkStates),
            Component = "spark",
            StartedAt = DateTime.UtcNow.AddMinutes(-Rng.Next(5, 120)),
            LastPolled = DateTime.UtcNow,
            Details = new() { ["project_id"] = $"proj-{(i % 2) + 1}", ["asset_id"] = $"spark-asset-{i}" }
        }).ToList();

    public static List<NormalizedJob> DataStageJobs() =>
        Enumerable.Range(1, 6).Select(i => new NormalizedJob
        {
            Id = $"proj-1/ds-job-{i}",
            Name = $"ETL Pipeline {i:D2}",
            Status = Rand(DataStageStates),
            Component = "datastage",
            StartedAt = DateTime.UtcNow.AddMinutes(-Rng.Next(3, 90)),
            LastPolled = DateTime.UtcNow,
            Details = new() { ["project_id"] = "proj-1", ["asset_id"] = $"ds-job-{i}" }
        }).ToList();

    public static List<NormalizedJob> FlinkJobs() =>
        Enumerable.Range(1, 5).Select(i => new NormalizedJob
        {
            Id = $"flink-job-{Guid.NewGuid():N}"[..16],
            Name = $"Flink Streaming Job {i}",
            Status = Rand(FlinkStates),
            Component = "flink",
            StartedAt = DateTime.UtcNow.AddMinutes(-Rng.Next(10, 300)),
            LastPolled = DateTime.UtcNow,
            Details = new() { ["cluster_url"] = "http://flink-jobmanager:8081" }
        }).ToList();

    public static List<NormalizedJob> EventProcessingFlows() =>
        Enumerable.Range(1, 4).Select(i => new NormalizedJob
        {
            Id = $"event-automation/flow-{i}",
            Name = $"Event Flow {i}",
            Status = Rand(K8sStates),
            Component = "event_processing",
            LastPolled = DateTime.UtcNow,
            Details = new() { ["namespace"] = "event-automation" }
        }).ToList();

    public static List<ApiCallLog> ApicLogs()
    {
        var apis = new[] { "customers-api", "orders-api", "payments-api", "inventory-api" };
        var methods = new[] { "GET", "POST", "PUT", "DELETE" };
        var statuses = new[] { 200, 200, 200, 200, 201, 400, 401, 404, 500, 502 };

        return Enumerable.Range(0, 200).Select(i => new ApiCallLog
        {
            Timestamp = DateTime.UtcNow.AddSeconds(-Rng.Next(0, 3600)),
            ApiName = apis[Rng.Next(apis.Length)],
            Method = methods[Rng.Next(methods.Length)],
            Path = $"/api/v1/resource/{Rng.Next(1, 100)}",
            StatusCode = statuses[Rng.Next(statuses.Length)],
            LatencyMs = Math.Round(20 + Math.Pow(Rng.NextDouble(), 2) * 980, 2),
            OrgName = "myorg",
            CatalogName = "sandbox",
            ConsumerOrg = $"consumer-{Rng.Next(1, 5)}",
            AppName = $"app-{Rng.Next(1, 3)}"
        }).ToList();
    }
}
