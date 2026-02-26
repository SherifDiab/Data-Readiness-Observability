import DataTable, { Column } from '../common/DataTable';
import { formatLatency, formatTimeAgo } from '../../utils/formatters';
import type { ApiCallLog } from '../../types/apic';

interface RecentLogsTableProps {
  logs: ApiCallLog[];
}

function methodColor(method: string): string {
  const colors: Record<string, string> = {
    GET: 'text-status-running',
    POST: 'text-accent',
    PUT: 'text-status-warning',
    DELETE: 'text-status-failed',
    PATCH: 'text-status-queued',
  };
  return colors[method] || 'text-text-secondary';
}

function statusColor(code: number): string {
  if (code >= 500) return 'text-status-failed';
  if (code >= 400) return 'text-status-warning';
  return 'text-status-running';
}

const columns: Column<ApiCallLog>[] = [
  {
    key: 'time',
    header: 'Time',
    render: (l) => <span className="text-xs text-text-tertiary">{formatTimeAgo(l.timestamp)}</span>,
    width: '100px',
  },
  {
    key: 'api',
    header: 'API',
    render: (l) => <span className="text-xs text-text-secondary">{l.api_name}</span>,
    width: '140px',
  },
  {
    key: 'method',
    header: 'Method',
    render: (l) => <span className={`text-xs font-mono font-bold ${methodColor(l.method)}`}>{l.method}</span>,
    width: '70px',
  },
  {
    key: 'path',
    header: 'Path',
    render: (l) => (
      <span className="text-xs font-mono text-text-secondary truncate max-w-[200px] block" title={l.path}>
        {l.path}
      </span>
    ),
  },
  {
    key: 'status',
    header: 'Status',
    render: (l) => (
      <span className={`text-xs font-mono font-bold ${statusColor(l.status_code)}`}>{l.status_code}</span>
    ),
    width: '70px',
  },
  {
    key: 'latency',
    header: 'Latency',
    render: (l) => <span className="text-xs font-mono text-text-secondary">{formatLatency(l.latency_ms)}</span>,
    width: '80px',
  },
];

export default function RecentLogsTable({ logs }: RecentLogsTableProps) {
  return (
    <DataTable
      columns={columns}
      data={logs.slice(0, 50)}
      rowKey={(l) => `${l.timestamp}-${l.path}`}
      emptyMessage="No API logs available"
    />
  );
}
