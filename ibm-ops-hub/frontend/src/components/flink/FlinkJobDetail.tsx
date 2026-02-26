import { X } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import { formatDuration, formatDateTime } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';

interface FlinkJobDetailProps {
  job: NormalizedJob | null;
  onClose: () => void;
}

export default function FlinkJobDetail({ job, onClose }: FlinkJobDetailProps) {
  if (!job) return null;

  const tasks = job.details?.tasks as Record<string, number> | undefined;
  const rootException = job.details?.root_exception as string | undefined;
  const lastCheckpoint = job.details?.last_checkpoint as string | undefined;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-[520px] bg-bg-secondary border-l border-border-color z-50 overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-border-color">
          <h3 className="font-mono font-bold text-text-primary truncate">{job.job_name}</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <div className="flex items-center gap-3">
            <StatusBadge status={job.status} />
            <span className="text-xs text-text-tertiary font-mono">{job.job_id}</span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-text-tertiary mb-1">Started</div>
              <div className="text-sm text-text-secondary">{formatDateTime(job.started_at)}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Duration</div>
              <div className="text-sm font-mono text-text-primary">{formatDuration(job.duration_seconds)}</div>
            </div>
          </div>

          {tasks && (
            <div>
              <h4 className="text-sm font-medium text-text-secondary mb-3">Task Breakdown</h4>
              <div className="grid grid-cols-3 gap-2">
                {Object.entries(tasks).map(([k, v]) => (
                  <div key={k} className="bg-bg-tertiary rounded-lg p-2 text-center">
                    <div className="text-lg font-mono font-bold text-text-primary">{v}</div>
                    <div className="text-xs text-text-tertiary capitalize">{k}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {rootException && (
            <div>
              <h4 className="text-sm font-medium text-status-failed mb-2">Root Exception</h4>
              <pre className="bg-bg-tertiary rounded-lg border border-status-failed/30 p-3 text-xs text-status-failed overflow-x-auto whitespace-pre-wrap break-all">
                {rootException}
              </pre>
            </div>
          )}

          {lastCheckpoint && (
            <div>
              <h4 className="text-sm font-medium text-text-secondary mb-2">Last Checkpoint</h4>
              <span className="text-xs font-mono text-text-secondary">{lastCheckpoint}</span>
            </div>
          )}
        </div>
      </div>
    </>
  );
}
