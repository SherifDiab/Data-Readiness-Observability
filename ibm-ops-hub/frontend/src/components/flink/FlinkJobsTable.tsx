import DataTable, { Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import { formatDuration } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';
import clsx from 'clsx';

interface FlinkJobsTableProps {
  jobs: NormalizedJob[];
  onJobClick?: (job: NormalizedJob) => void;
}

function TasksBar({ tasks }: { tasks: Record<string, number> | undefined }) {
  if (!tasks || !tasks.total) return <span className="text-xs text-text-tertiary">-</span>;
  const { total, running = 0, finished = 0, failed = 0 } = tasks;
  return (
    <div className="flex items-center gap-2">
      <div className="flex h-2 w-20 rounded-full overflow-hidden bg-bg-hover">
        <div className="bg-status-running" style={{ width: `${(running / total) * 100}%` }} />
        <div className="bg-status-completed" style={{ width: `${(finished / total) * 100}%` }} />
        <div className="bg-status-failed" style={{ width: `${(failed / total) * 100}%` }} />
      </div>
      <span className="text-xs font-mono text-text-tertiary">{running}/{total}</span>
    </div>
  );
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
    header: 'State',
    render: (j) => <StatusBadge status={j.status} />,
    width: '110px',
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
    key: 'tasks',
    header: 'Tasks',
    render: (j) => <TasksBar tasks={j.details?.tasks as Record<string, number>} />,
    width: '160px',
  },
  {
    key: 'exceptions',
    header: 'Exceptions',
    render: (j) => {
      const exc = j.details?.root_exception;
      return exc ? (
        <span className="text-xs text-status-failed font-mono">1</span>
      ) : (
        <span className="text-xs text-text-tertiary">-</span>
      );
    },
    width: '90px',
  },
];

export default function FlinkJobsTable({ jobs, onJobClick }: FlinkJobsTableProps) {
  return (
    <DataTable
      columns={columns}
      data={jobs}
      rowKey={(j) => j.job_id}
      onRowClick={onJobClick}
      rowClassName={(j) =>
        clsx(j.status === 'Failed' && 'row-failed', j.status === 'Running' && 'row-running')
      }
      emptyMessage="No Flink jobs found"
    />
  );
}
