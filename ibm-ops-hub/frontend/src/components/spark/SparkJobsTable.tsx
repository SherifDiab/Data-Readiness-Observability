import DataTable, { Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import { formatDuration } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';
import clsx from 'clsx';

interface SparkJobsTableProps {
  jobs: NormalizedJob[];
  onJobClick?: (job: NormalizedJob) => void;
}

const columns: Column<NormalizedJob>[] = [
  {
    key: 'job_name',
    header: 'Job Name',
    render: (j) => (
      <span className="font-medium text-text-primary font-mono text-xs">{j.job_name}</span>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    render: (j) => <StatusBadge status={j.status} />,
    width: '120px',
  },
  {
    key: 'started_at',
    header: 'Started',
    render: (j) => <TimeAgo date={j.started_at} />,
    width: '150px',
  },
  {
    key: 'duration',
    header: 'Duration',
    render: (j) => (
      <span className="font-mono text-xs text-text-secondary">
        {formatDuration(j.duration_seconds)}
      </span>
    ),
    width: '100px',
  },
  {
    key: 'project',
    header: 'Project',
    render: (j) => (
      <span className="text-xs text-text-secondary">
        {(j.details?.project_id as string) || '-'}
      </span>
    ),
    width: '160px',
  },
];

export default function SparkJobsTable({ jobs, onJobClick }: SparkJobsTableProps) {
  return (
    <DataTable
      columns={columns}
      data={jobs}
      rowKey={(j) => j.job_id}
      onRowClick={onJobClick}
      rowClassName={(j) =>
        clsx(j.status === 'Failed' && 'row-failed', j.status === 'Running' && 'row-running')
      }
      emptyMessage="No Spark jobs found"
    />
  );
}
