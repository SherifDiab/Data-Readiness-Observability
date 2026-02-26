import DataTable, { Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import { formatDuration, formatNumber } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';
import clsx from 'clsx';

interface DataStageJobsTableProps {
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
    width: '130px',
  },
  {
    key: 'duration',
    header: 'Duration',
    render: (j) => (
      <span className="font-mono text-xs text-text-secondary">{formatDuration(j.duration_seconds)}</span>
    ),
    width: '90px',
  },
  {
    key: 'rows_read',
    header: 'Rows Read',
    render: (j) => (
      <span className="font-mono text-xs text-text-secondary">
        {formatNumber(j.details?.rows_read as number)}
      </span>
    ),
    width: '100px',
  },
  {
    key: 'rows_written',
    header: 'Rows Written',
    render: (j) => (
      <span className="font-mono text-xs text-text-secondary">
        {formatNumber(j.details?.rows_written as number)}
      </span>
    ),
    width: '110px',
  },
  {
    key: 'warnings',
    header: 'Warnings',
    render: (j) => {
      const w = j.details?.warnings_count as number;
      return w ? (
        <span className="font-mono text-xs text-status-warning">{w}</span>
      ) : (
        <span className="text-xs text-text-tertiary">-</span>
      );
    },
    width: '80px',
  },
];

export default function DataStageJobsTable({ jobs, onJobClick }: DataStageJobsTableProps) {
  return (
    <DataTable
      columns={columns}
      data={jobs}
      rowKey={(j) => j.job_id}
      onRowClick={onJobClick}
      rowClassName={(j) =>
        clsx(j.status === 'Failed' && 'row-failed', j.status === 'Running' && 'row-running')
      }
      emptyMessage="No DataStage jobs found"
    />
  );
}
