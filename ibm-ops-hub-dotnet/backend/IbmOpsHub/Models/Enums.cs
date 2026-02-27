namespace IbmOpsHub.Models;

public enum JobStatus
{
    Running,
    Completed,
    Failed,
    Warning,
    Unknown,
    Queued,
    Canceled,
    Suspended,
    Restarting
}

public enum ComponentStatus
{
    Healthy,
    Degraded,
    Down,
    Unknown
}
