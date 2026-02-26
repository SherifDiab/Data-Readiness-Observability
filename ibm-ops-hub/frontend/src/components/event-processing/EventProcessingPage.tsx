import { useState } from 'react';
import { Radio } from 'lucide-react';
import { useEventProcessingFlows } from '../../hooks/useJobs';
import FlowsTable from './FlowsTable';
import FlowDetail from './FlowDetail';
import LoadingSkeleton from '../common/LoadingSkeleton';
import ErrorState from '../common/ErrorState';
import MetricCard from '../common/MetricCard';
import type { NormalizedJob } from '../../types/dashboard';

export default function EventProcessingPage() {
  const { data: flows, isLoading, error, refetch } = useEventProcessingFlows();
  const [selectedFlow, setSelectedFlow] = useState<NormalizedJob | null>(null);
  const [searchQuery, setSearchQuery] = useState('');

  if (isLoading) return <LoadingSkeleton rows={8} />;
  if (error) return <ErrorState message="Failed to load Event Processing flows" onRetry={refetch} />;

  const allFlows = flows || [];
  const filtered = allFlows.filter((f) => {
    if (searchQuery && !f.job_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const running = allFlows.filter((f) => f.status === 'Running').length;
  const failed = allFlows.filter((f) => f.status === 'Failed').length;
  const suspended = allFlows.filter((f) => f.status === 'Suspended').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Radio size={24} className="text-accent" />
        <h2 className="text-xl font-mono font-bold">Event Processing Flows</h2>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Flows" value={allFlows.length} />
        <MetricCard title="Running" value={running} className="border-l-2 border-l-status-running" />
        <MetricCard title="Failed" value={failed} className="border-l-2 border-l-status-failed" />
        <MetricCard title="Suspended" value={suspended} className="border-l-2 border-l-status-suspended" />
      </div>

      <div className="flex items-center gap-4">
        <input
          type="text"
          placeholder="Search by flow name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-bg-tertiary border border-border-color rounded-lg px-4 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent w-64"
        />
      </div>

      <FlowsTable flows={filtered} onFlowClick={setSelectedFlow} />
      <FlowDetail flow={selectedFlow} onClose={() => setSelectedFlow(null)} />
    </div>
  );
}
