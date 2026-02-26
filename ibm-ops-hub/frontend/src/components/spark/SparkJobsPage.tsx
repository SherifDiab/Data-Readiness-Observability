import { useState } from 'react';
import { Zap } from 'lucide-react';
import { useSparkJobs } from '../../hooks/useJobs';
import SparkJobsTable from './SparkJobsTable';
import SparkJobDetail from './SparkJobDetail';
import LoadingSkeleton from '../common/LoadingSkeleton';
import ErrorState from '../common/ErrorState';
import MetricCard from '../common/MetricCard';
import type { NormalizedJob } from '../../types/dashboard';

export default function SparkJobsPage() {
  const { data: jobs, isLoading, error, refetch } = useSparkJobs();
  const [selectedJob, setSelectedJob] = useState<NormalizedJob | null>(null);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  if (isLoading) return <LoadingSkeleton rows={8} />;
  if (error) return <ErrorState message="Failed to load Spark jobs" onRetry={refetch} />;

  const allJobs = jobs || [];
  const filtered = allJobs.filter((j) => {
    if (statusFilter && j.status !== statusFilter) return false;
    if (searchQuery && !j.job_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const running = allJobs.filter((j) => j.status === 'Running').length;
  const failed = allJobs.filter((j) => j.status === 'Failed').length;
  const completed = allJobs.filter((j) => j.status === 'Completed').length;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Zap size={24} className="text-accent" />
        <h2 className="text-xl font-mono font-bold">Spark Jobs</h2>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Jobs" value={allJobs.length} />
        <MetricCard title="Running" value={running} className="border-l-2 border-l-status-running" />
        <MetricCard title="Failed" value={failed} className="border-l-2 border-l-status-failed" />
        <MetricCard title="Completed" value={completed} className="border-l-2 border-l-status-completed" />
      </div>

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
          <option value="">All Statuses</option>
          <option value="Running">Running</option>
          <option value="Completed">Completed</option>
          <option value="Failed">Failed</option>
          <option value="Queued">Queued</option>
          <option value="Canceled">Canceled</option>
        </select>
      </div>

      <SparkJobsTable jobs={filtered} onJobClick={setSelectedJob} />
      <SparkJobDetail job={selectedJob} onClose={() => setSelectedJob(null)} />
    </div>
  );
}
