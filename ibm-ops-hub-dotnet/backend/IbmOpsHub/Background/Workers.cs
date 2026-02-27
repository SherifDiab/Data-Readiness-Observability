using IbmOpsHub.Configuration;
using IbmOpsHub.Hubs;
using IbmOpsHub.Services;
using Microsoft.AspNetCore.SignalR;
using Microsoft.Extensions.Options;

namespace IbmOpsHub.Background;

public class SparkPollingWorker(SparkService svc, IHubContext<OpsHub> hub, IOptions<AppSettings> opts, ILogger<SparkPollingWorker> log)
    : PollingWorker<SparkService>(svc, hub, log)
{
    protected override int PollIntervalSeconds => opts.Value.SparkPollInterval;
}

public class DataStagePollingWorker(DataStageService svc, IHubContext<OpsHub> hub, IOptions<AppSettings> opts, ILogger<DataStagePollingWorker> log)
    : PollingWorker<DataStageService>(svc, hub, log)
{
    protected override int PollIntervalSeconds => opts.Value.DatastagePollInterval;
}

public class FlinkPollingWorker(FlinkService svc, IHubContext<OpsHub> hub, IOptions<AppSettings> opts, ILogger<FlinkPollingWorker> log)
    : PollingWorker<FlinkService>(svc, hub, log)
{
    protected override int PollIntervalSeconds => opts.Value.FlinkPollInterval;
}

public class EventProcessingPollingWorker(EventProcessingService svc, IHubContext<OpsHub> hub, IOptions<AppSettings> opts, ILogger<EventProcessingPollingWorker> log)
    : PollingWorker<EventProcessingService>(svc, hub, log)
{
    protected override int PollIntervalSeconds => opts.Value.EventProcessingPollInterval;
}

public class ApicPollingWorker(ApicService svc, IHubContext<OpsHub> hub, IOptions<AppSettings> opts, ILogger<ApicPollingWorker> log)
    : PollingWorker<ApicService>(svc, hub, log)
{
    protected override int PollIntervalSeconds => opts.Value.ApicPollInterval;
}
