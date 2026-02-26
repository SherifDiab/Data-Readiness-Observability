import { X } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import { formatDuration, formatDateTime, formatNumber } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';

interface DataStageJobDetailProps {
  job: NormalizedJob | null;
  onClose: () => void;
}

export default function DataStageJobDetail({ job, onClose }: DataStageJobDetailProps) {
  if (!job) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-[480px] bg-bg-secondary border-l border-border-color z-50 overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-border-color">
          <h3 className="font-mono font-bold text-text-primary truncate">{job.job_name}</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <StatusBadge status={job.status} />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-text-tertiary mb-1">Started</div>
              <div className="text-sm text-text-secondary">{formatDateTime(job.started_at)}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Duration</div>
              <div className="text-sm font-mono text-text-primary">{formatDuration(job.duration_seconds)}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Rows Read</div>
              <div className="text-sm font-mono text-text-primary">
                {formatNumber(job.details?.rows_read as number)}
              </div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Rows Written</div>
              <div className="text-sm font-mono text-text-primary">
                {formatNumber(job.details?.rows_written as number)}
              </div>
            </div>
          </div>
          {(job.details?.flow_name || job.details?.project_name) && (
            <div className="bg-bg-tertiary rounded-lg border border-border-color p-3 space-y-2">
              {job.details.flow_name && (
                <div className="flex gap-2 text-xs">
                  <span className="text-text-tertiary min-w-[100px]">Flow Name:</span>
                  <span className="text-text-primary">{String(job.details.flow_name)}</span>
                </div>
              )}
              {job.details.project_name && (
                <div className="flex gap-2 text-xs">
                  <span className="text-text-tertiary min-w-[100px]">Project:</span>
                  <span className="text-text-primary">{String(job.details.project_name)}</span>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}
