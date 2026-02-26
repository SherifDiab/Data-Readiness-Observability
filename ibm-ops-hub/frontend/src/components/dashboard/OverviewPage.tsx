import { Zap, Database, Radio, Activity, Globe, AlertTriangle } from 'lucide-react';
import { useDashboardSummary } from '../../hooks/useDashboard';
import MetricCard from '../common/MetricCard';
import StatusBadge from '../common/StatusBadge';
import LoadingSkeleton from '../common/LoadingSkeleton';
import ErrorState from '../common/ErrorState';
import HealthRing from './HealthRing';
import AlertBanner from './AlertBanner';
import TimeAgo from '../common/TimeAgo';
import { formatNumber } from '../../utils/formatters';
import type { ComponentHealth, NormalizedJob, JobStatus } from '../../types/dashboard';

const componentIcons: Record<string, typeof Zap> = {
  spark: Zap,
  datastage: Database,
  event_processing: Radio,
  flink: Activity,
  apic: Globe,
};

const componentLabels: Record<string, string> = {
  spark: 'Spark Jobs',
  datastage: 'DataStage',
  event_processing: 'Event Processing',
  flink: 'Flink Jobs',
  apic: 'API Connect',
};

export default function OverviewPage() {
  const { data: summary, isLoading, error, refetch } = useDashboardSummary();

  if (isLoading) return <LoadingSkeleton rows={3} />;
  if (error) return <ErrorState message="Failed to load dashboard summary" onRetry={refetch} />;
  if (!summary) return <ErrorState message="No data available" />;

  const recentFailures = summary.components
    .filter((c) => c.failed > 0)
    .map((c) => `${componentLabels[c.component]}: ${c.failed} failed`);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-mono font-bold">System Overview</h2>
        <span className="text-xs text-text-tertiary">
          Last updated: <TimeAgo date={summary.last_updated} />
        </span>
      </div>

      {summary.critical_alerts.length > 0 && (
        <AlertBanner alerts={summary.critical_alerts} />
      )}

      <div className="grid grid-cols-5 gap-4">
        {summary.components.map((comp: ComponentHealth) => {
          const Icon = componentIcons[comp.component] || Activity;
          return (
            <div
              key={comp.component}
              className="bg-bg-tertiary rounded-xl border border-border-color p-4"
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Icon size={18} className="text-accent" />
                  <span className="text-sm font-medium">{componentLabels[comp.component]}</span>
                </div>
                <div className={`w-2 h-2 rounded-full ${comp.is_reachable ? 'bg-status-running status-running-pulse' : 'bg-status-failed'}`} />
              </div>
              <HealthRing
                running={comp.running}
                completed={comp.completed}
                failed={comp.failed}
                warning={comp.warning}
                other={comp.other}
                label={componentLabels[comp.component]}
              />
              <div className="mt-3 grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-lg font-mono font-bold text-status-running">{comp.running}</div>
                  <div className="text-xs text-text-tertiary">Running</div>
                </div>
                <div>
                  <div className="text-lg font-mono font-bold text-status-failed">{comp.failed}</div>
                  <div className="text-xs text-text-tertiary">Failed</div>
                </div>
                <div>
                  <div className="text-lg font-mono font-bold text-text-secondary">{comp.total_jobs}</div>
                  <div className="text-xs text-text-tertiary">Total</div>
                </div>
              </div>
              <div className="mt-2 text-xs text-text-tertiary">
                <TimeAgo date={comp.last_polled_at} />
              </div>
            </div>
          );
        })}
      </div>

      {summary.total_failures > 0 && (
        <div className="bg-bg-tertiary rounded-xl border border-border-color">
          <div className="flex items-center gap-2 p-4 border-b border-border-color">
            <AlertTriangle size={16} className="text-status-failed" />
            <h3 className="text-sm font-medium">Recent Failures ({summary.total_failures})</h3>
          </div>
          <div className="p-4">
            {recentFailures.map((msg, i) => (
              <div key={i} className="flex items-center gap-2 py-2 text-sm text-text-secondary">
                <span className="w-2 h-2 rounded-full bg-status-failed" />
                {msg}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
