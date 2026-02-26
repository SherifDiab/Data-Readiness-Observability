import { useState } from 'react';
import { Globe } from 'lucide-react';
import { useApicLogs, useApicSummary } from '../../hooks/useJobs';
import MetricCard from '../common/MetricCard';
import LoadingSkeleton from '../common/LoadingSkeleton';
import ErrorState from '../common/ErrorState';
import ApiCallsChart from './ApiCallsChart';
import ErrorRateChart from './ErrorRateChart';
import TopErrorsTable from './TopErrorsTable';
import RecentLogsTable from './RecentLogsTable';
import { formatNumber, formatLatency, formatPercent } from '../../utils/formatters';

const timeRanges = ['last15m', 'last1hour', 'last6hours', 'last24hours'] as const;
const timeRangeLabels: Record<string, string> = {
  last15m: 'Last 15m',
  last1hour: 'Last 1h',
  last6hours: 'Last 6h',
  last24hours: 'Last 24h',
};

export default function ApiConnectPage() {
  const [timeframe, setTimeframe] = useState('last1hour');
  const { data: summary, isLoading: summaryLoading, error: summaryError, refetch: refetchSummary } = useApicSummary(timeframe);
  const { data: logs, isLoading: logsLoading, error: logsError, refetch: refetchLogs } = useApicLogs({ timeframe });

  const isLoading = summaryLoading || logsLoading;
  const error = summaryError || logsError;

  if (isLoading) return <LoadingSkeleton rows={6} />;
  if (error) return <ErrorState message="Failed to load API Connect data" onRetry={() => { refetchSummary(); refetchLogs(); }} />;

  const errorRateData = summary?.calls_by_minute?.map((d) => ({
    minute: d.minute,
    rate: summary.error_rate_percent,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Globe size={24} className="text-accent" />
          <h2 className="text-xl font-mono font-bold">API Connect</h2>
        </div>
        <div className="flex gap-1 bg-bg-tertiary rounded-lg p-1 border border-border-color">
          {timeRanges.map((tr) => (
            <button
              key={tr}
              onClick={() => setTimeframe(tr)}
              className={`px-3 py-1 text-xs rounded-md transition-colors ${
                timeframe === tr
                  ? 'bg-accent text-white'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {timeRangeLabels[tr]}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Calls" value={formatNumber(summary?.total_calls)} />
        <MetricCard
          title="Error Rate"
          value={formatPercent(summary?.error_rate_percent)}
          className="border-l-2 border-l-status-failed"
        />
        <MetricCard title="Avg Latency" value={formatLatency(summary?.avg_latency_ms)} />
        <MetricCard
          title="P95 Latency"
          value={formatLatency(summary?.p95_latency_ms)}
          className="border-l-2 border-l-status-warning"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div className="bg-bg-tertiary rounded-xl border border-border-color p-4">
          <h3 className="text-sm font-medium text-text-secondary mb-4">API Calls / Minute</h3>
          <ApiCallsChart data={summary?.calls_by_minute || []} />
        </div>
        <div className="bg-bg-tertiary rounded-xl border border-border-color p-4">
          <h3 className="text-sm font-medium text-text-secondary mb-4">Error Rate Trend</h3>
          <ErrorRateChart data={errorRateData} />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h3 className="text-sm font-medium text-text-secondary mb-3">Top Errors</h3>
          <TopErrorsTable errors={summary?.top_errors || []} />
        </div>
        <div>
          <h3 className="text-sm font-medium text-text-secondary mb-3">Recent API Calls</h3>
          <RecentLogsTable logs={logs || []} />
        </div>
      </div>
    </div>
  );
}
