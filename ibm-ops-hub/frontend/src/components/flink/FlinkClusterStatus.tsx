import type { FlinkClusterOverview } from '../../types/flink';

interface FlinkClusterStatusProps {
  cluster: FlinkClusterOverview | undefined;
}

export default function FlinkClusterStatus({ cluster }: FlinkClusterStatusProps) {
  if (!cluster) {
    return (
      <div className="bg-bg-tertiary rounded-xl border border-border-color p-4 text-text-tertiary text-sm">
        Cluster info unavailable
      </div>
    );
  }

  const slotsUsed = cluster.slots_total - cluster.slots_available;

  return (
    <div className="bg-bg-tertiary rounded-xl border border-border-color p-4">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-text-secondary">Cluster Status</h3>
        <span className="text-xs font-mono text-accent">Flink {cluster.flink_version}</span>
      </div>
      <div className="grid grid-cols-6 gap-4">
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-text-primary">{cluster.taskmanagers}</div>
          <div className="text-xs text-text-tertiary">Task Managers</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-text-primary">{cluster.slots_total}</div>
          <div className="text-xs text-text-tertiary">Total Slots</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-status-running">{cluster.slots_available}</div>
          <div className="text-xs text-text-tertiary">Free Slots</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-status-running">{cluster.jobs_running}</div>
          <div className="text-xs text-text-tertiary">Running</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-status-completed">{cluster.jobs_finished}</div>
          <div className="text-xs text-text-tertiary">Finished</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-status-failed">{cluster.jobs_failed}</div>
          <div className="text-xs text-text-tertiary">Failed</div>
        </div>
      </div>
      <div className="mt-3">
        <div className="flex justify-between text-xs text-text-tertiary mb-1">
          <span>Slot utilization</span>
          <span>{slotsUsed}/{cluster.slots_total}</span>
        </div>
        <div className="h-1.5 bg-bg-hover rounded-full overflow-hidden">
          <div
            className="h-full bg-accent rounded-full transition-all"
            style={{ width: `${cluster.slots_total > 0 ? (slotsUsed / cluster.slots_total) * 100 : 0}%` }}
          />
        </div>
      </div>
    </div>
  );
}
