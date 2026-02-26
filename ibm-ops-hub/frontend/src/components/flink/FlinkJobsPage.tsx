import { useState } from 'react';
import { Activity } from 'lucide-react';
import { useFlinkJobs, useFlinkCluster } from '../../hooks/useJobs';
import FlinkJobsTable from './FlinkJobsTable';
import FlinkJobDetail from './FlinkJobDetail';
import FlinkClusterStatus from './FlinkClusterStatus';
import LoadingSkeleton from '../common/LoadingSkeleton';
import ErrorState from '../common/ErrorState';
import type { NormalizedJob } from '../../types/dashboard';

export default function FlinkJobsPage() {
  const { data: jobs, isLoading, error, refetch } = useFlinkJobs();
  const { data: cluster } = useFlinkCluster();
  const [selectedJob, setSelectedJob] = useState<NormalizedJob | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  if (isLoading) return <LoadingSkeleton rows={8} />;
  if (error) return <ErrorState message="Failed to load Flink jobs" onRetry={refetch} />;

  const allJobs = jobs || [];
  const filtered = allJobs.filter((j) => {
    if (statusFilter && j.status !== statusFilter) return false;
    if (searchQuery && !j.job_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Activity size={24} className="text-accent" />
        <h2 className="text-xl font-mono font-bold">Flink Jobs</h2>
      </div>

      <FlinkClusterStatus cluster={cluster} />

      <div className="flex items-center gap-4">
        <input
          type="text"
          placeholder="Search by job name..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="bg-bg-tertiary border border-border-color rounded-lg px-4 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent w-64"
        />
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="bg-bg-tertiary border border-border-color rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-accent"
        >
          <option value="">All States</option>
          <option value="Running">Running</option>
          <option value="Completed">Completed</option>
          <option value="Failed">Failed</option>
          <option value="Canceled">Canceled</option>
          <option value="Restarting">Restarting</option>
          <option value="Suspended">Suspended</option>
        </select>
      </div>

      <FlinkJobsTable jobs={filtered} onJobClick={setSelectedJob} />
      <FlinkJobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
    </div>
  );
}
