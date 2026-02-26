import { X } from 'lucide-react';
import StatusBadge from '../common/StatusBadge';
import TimeAgo from '../common/TimeAgo';
import { formatDateTime } from '../../utils/formatters';
import type { NormalizedJob } from '../../types/dashboard';

interface FlowDetailProps {
  flow: NormalizedJob | null;
  onClose: () => void;
}

export default function FlowDetail({ flow, onClose }: FlowDetailProps) {
  if (!flow) return null;

  const details = flow.details || {};

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-[480px] bg-bg-secondary border-l border-border-color z-50 overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-border-color">
          <h3 className="font-mono font-bold text-text-primary truncate">{flow.job_name}</h3>
          <button onClick={onClose} className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary">
            <X size={18} />
          </button>
        </div>
        <div className="p-6 space-y-6">
          <StatusBadge status={flow.status} />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-text-tertiary mb-1">Flow ID</div>
              <div className="text-xs font-mono text-text-secondary break-all">{flow.job_id}</div>
            </div>
            <div>
              <div className="text-xs text-text-tertiary mb-1">Started</div>
              <div className="text-sm text-text-secondary">{formatDateTime(flow.started_at)}</div>
            </div>
          </div>

          <div className="bg-bg-tertiary rounded-lg border border-border-color p-3 space-y-2">
            {[
              ['JM Deployment Status', details.jm_deployment_status],
              ['Reconciliation Status', details.reconciliation_status],
              ['Parallelism', details.parallelism],
              ['Flink Image', details.flink_image],
              ['Last Savepoint', details.last_savepoint_timestamp],
            ].map(([label, val]) => val != null && (
              <div key={String(label)} className="flex gap-2 text-xs">
                <span className="text-text-tertiary min-w-[160px]">{String(label)}:</span>
                <span className="text-text-primary">{String(val)}</span>
              </div>
            ))}
          </div>

          {flow.native_url && (
            <a href={flow.native_url} target="_blank" rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm text-accent hover:underline">
              Open in Event Processing UI →
            </a>
          )}
        </div>
      </div>
    </>
  );
}
