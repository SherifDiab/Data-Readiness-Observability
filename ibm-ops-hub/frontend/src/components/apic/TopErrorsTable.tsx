interface TopError {
  status_code: number;
  api: string;
  count: number;
}

interface TopErrorsTableProps {
  errors: TopError[];
}

function statusCodeColor(code: number): string {
  if (code >= 500) return 'text-status-failed';
  if (code >= 400) return 'text-status-warning';
  return 'text-text-secondary';
}

export default function TopErrorsTable({ errors }: TopErrorsTableProps) {
  if (errors.length === 0) {
    return (
      <div className="bg-bg-tertiary rounded-xl border border-border-color p-6 text-center text-text-tertiary text-sm">
        No errors
      </div>
    );
  }

  return (
    <div className="bg-bg-tertiary rounded-xl border border-border-color overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border-color">
            <th className="text-left px-4 py-2 text-xs font-medium text-text-tertiary uppercase">Status</th>
            <th className="text-left px-4 py-2 text-xs font-medium text-text-tertiary uppercase">API</th>
            <th className="text-right px-4 py-2 text-xs font-medium text-text-tertiary uppercase">Count</th>
          </tr>
        </thead>
        <tbody>
          {errors.map((e, i) => (
            <tr key={i} className="border-b border-border-color/50 hover:bg-bg-hover">
              <td className={`px-4 py-2 font-mono text-xs font-bold ${statusCodeColor(e.status_code)}`}>
                {e.status_code}
              </td>
              <td className="px-4 py-2 text-xs text-text-secondary">{e.api}</td>
              <td className="px-4 py-2 text-xs font-mono text-text-primary text-right">{e.count}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
