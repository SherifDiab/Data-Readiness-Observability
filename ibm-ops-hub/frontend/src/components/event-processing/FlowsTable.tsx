import DataTable, { Column } from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import type { NormalizedJob } from '../../types/dashboard';
import clsx from 'clsx';

interface FlowsTableProps {
  flows: NormalizedJob[];
  onFlowClick?: (flow: NormalizedJob) => void;
}

const columns: Column<NormalizedJob>[] = [
  {
    key: 'job_name',
    header: 'Flow Name',
    render: (j) => (
      <span className="font-medium text-text-primary font-mono text-xs">{j.job_name}</span>
    ),
  },
  {
    key: 'status',
    header: 'Flink State',
    render: (j) => <StatusBadge status={j.status} />,
    width: '120px',
  },
  {
    key: 'jm_status',
    header: 'JM Status',
    render: (j) => {
      const jmStatus = j.details?.jm_deployment_status as string;
      const color = jmStatus === 'READY' ? 'text-status-running' : jmStatus === 'ERROR' ? 'text-status-failed' : 'text-text-secondary';
      return <span className={`text-xs font-mono ${color}`}>{jmStatus || '-'}</span>;
    },
    width: '110px',
  },
  {
    key: 'parallelism',
    header: 'Parallelism',
    render: (j) => (
      <span className="font-mono text-xs text-text-secondary">
        {(j.details?.parallelism as number) || '-'}
      </span>
    ),
    width: '100px',
  },
  {
    key: 'savepoint',
    header: 'Last Savepoint',
    render: (j) => <TimeAgo date={j.details?.last_savepoint_timestamp as string} />,
    width: '140px',
  },
  {
    key: 'reconciliation',
    header: 'Reconciliation',
    render: (j) => {
      const rc = j.details?.reconciliation_status as string;
      return <span className="text-xs text-text-tertiary">{rc || '-'}</span>;
    },
    width: '120px',
  },
];

export default function FlowsTable({ flows, onFlowClick }: FlowsTableProps) {
  return (
    <DataTable
      columns={columns}
      data={flows}
      rowKey={(j) => j.job_id}
      onRowClick={onFlowClick}
      rowClassName={(j) =>
        clsx(j.status === 'Failed' && 'row-failed', j.status === 'Running' && 'row-running')
      }
      emptyMessage="No Event Processing flows found"
    />
  );
}
