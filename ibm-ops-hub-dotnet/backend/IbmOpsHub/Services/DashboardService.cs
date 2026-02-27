using IbmOpsHub.Models;
using IbmOpsHub.Services.Interfaces;

namespace IbmOpsHub.Services;

public class DashboardService(
    SparkService spark,
    DataStageService datastage,
    FlinkService flink,
    EventProcessingService eventProcessing,
    ApicService apic)
{
    public async Task<DashboardSummary> GetSummaryAsync()
    {
        var allServices = new[] { (IJobService)spark, datastage, flink, eventProcessing };
        var allJobLists = await Task.WhenAll(allServices.Select(s => s.GetCachedAsync()));
        var allJobs = allJobLists.SelectMany(j => j).ToList();

        var healthList = allServices.Select(s =>
        {
            var jobs = allJobLists[Array.IndexOf(allServices, s)];
            return BuildHealth(s.Component, jobs);
        }).ToList();

        return new DashboardSummary
        {
            TotalJobs = allJobs.Count,
            RunningJobs = allJobs.Count(j => j.Status == JobStatus.Running),
            FailedJobs = allJobs.Count(j => j.Status == JobStatus.Failed),
            CompletedJobs = allJobs.Count(j => j.Status == JobStatus.Completed),
            HealthyComponents = healthList.Count(h => h.Status == ComponentStatus.Healthy),
            DegradedComponents = healthList.Count(h => h.Status is ComponentStatus.Degraded or ComponentStatus.Down),
            RecentFailures = allJobs
                .Where(j => j.Status == JobStatus.Failed)
                .OrderByDescending(j => j.LastPolled)
                .Take(10)
                .ToList(),
            ComponentHealthList = healthList
        };
    }

    public async Task<List<ComponentHealth>> GetHealthAsync()
    {
        var services = new[] { (IJobService)spark, datastage, flink, eventProcessing };
        var tasks = services.Select(async s => BuildHealth(s.Component, await s.GetCachedAsync())).ToList();
        return (await Task.WhenAll(tasks)).ToList();
    }

    private static ComponentHealth BuildHealth(string component, List<NormalizedJob> jobs) => new()
    {
        Component = component,
        TotalJobs = jobs.Count,
        RunningJobs = jobs.Count(j => j.Status == JobStatus.Running),
        FailedJobs = jobs.Count(j => j.Status == JobStatus.Failed),
        CompletedJobs = jobs.Count(j => j.Status == JobStatus.Completed),
        LastPolled = jobs.MaxBy(j => j.LastPolled)?.LastPolled,
        Status = jobs.Count == 0 ? ComponentStatus.Unknown
            : jobs.Any(j => j.Status == JobStatus.Failed) ? ComponentStatus.Degraded
            : ComponentStatus.Healthy
    };
}
