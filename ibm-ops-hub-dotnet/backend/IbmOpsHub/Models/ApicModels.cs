namespace IbmOpsHub.Models;

public class ApiCallLog
{
    public string Id { get; set; } = Guid.NewGuid().ToString();
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
    public string ApiName { get; set; } = string.Empty;
    public string Method { get; set; } = string.Empty;
    public string Path { get; set; } = string.Empty;
    public int StatusCode { get; set; }
    public double LatencyMs { get; set; }
    public string OrgName { get; set; } = string.Empty;
    public string CatalogName { get; set; } = string.Empty;
    public string ConsumerOrg { get; set; } = string.Empty;
    public string AppName { get; set; } = string.Empty;
}

public class ApicSummary
{
    public long TotalCalls { get; set; }
    public long ErrorCalls { get; set; }
    public double ErrorRatePercent { get; set; }
    public double AvgLatencyMs { get; set; }
    public double P95LatencyMs { get; set; }
    public List<TopError> TopErrors { get; set; } = [];
    public List<CallsByMinute> CallsByMinute { get; set; } = [];
    public string Timeframe { get; set; } = "1h";
}

public class TopError
{
    public int StatusCode { get; set; }
    public string ApiName { get; set; } = string.Empty;
    public int Count { get; set; }
}

public class CallsByMinute
{
    public DateTime Minute { get; set; }
    public int Calls { get; set; }
    public int Errors { get; set; }
}
