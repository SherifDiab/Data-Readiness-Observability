import clsx from 'clsx';
import { JobStatus } from '../../types/dashboard';
import { statusColors, statusDotColors } from '../../utils/statusColors';

interface StatusBadgeProps {
  status: JobStatus;
  size?: 'sm' | 'md';
}

export default function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full border font-medium',
        statusColors[status] || statusColors.Unknown,
        size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs'
      )}
    >
      <span
        className={clsx(
          'w-1.5 h-1.5 rounded-full',
          statusDotColors[status] || statusDotColors.Unknown,
          status === 'Running' && 'status-running-pulse'
        )}
      />
      {status}
    </span>
  );
}
