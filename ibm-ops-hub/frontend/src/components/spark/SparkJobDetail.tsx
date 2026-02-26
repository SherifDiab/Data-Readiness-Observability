import { X } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import { formatDuration, formatDateTime } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';

interface SparkJobDetailProps {
  job: NormalizedJob | null;
  onClose: () => void;
}

export default function SparkJobDetail({ job, onClose }: SparkJobDetailProps) {
  if (!job) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-[480px] bg-bg-secondary border-l border-border-color z-50 overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-border-color">
          <h3 className="font-mono font-bold text-text-primary truncate">{job.job_name}</h3>
          <button
            onClick={onClose}
            className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text-primary"
          >
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
              <div className="text-xs text-text-tertiary mb-1">Finished</div>
              <div className="text-sm text-text-secondary">{formatDateTime(job.finished_at)}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Duration</div>
              <div className="text-sm font-mono text-text-primary">{formatDuration(job.duration_seconds)}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Last Updated</div>
              <div className="text-sm text-text-secondary"><TimeAgo date={job.last_polled_at} /></div>
            </div>
          </div>

          {job.details && Object.keys(job.details).length > 0 && (
            <div>
              <h4 className="text-sm font-medium text-text-secondary mb-3">Details</h4>
              <div className="bg-bg-tertiary rounded-lg border border-border-color p-3 space-y-2">
                {Object.entries(job.details).map(([k, v]) => (
                  <div key={k} className="flex gap-2 text-xs">
                    <span className="text-text-tertiary min-w-[120px] font-mono">{k}:</span>
                    <span className="text-text-primary break-all">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {job.native_url && (
            <a
              href={job.native_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-accent hover:underline"
            >
              Open in IBM UI →
            </a>
          )}
        </div>
      </div>
    </>
  );
}
