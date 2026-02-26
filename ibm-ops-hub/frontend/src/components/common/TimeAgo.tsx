import { formatTimeAgo, formatDateTime } from '../../utils/formatters';

interface TimeAgoProps {
  date: string | null | undefined;
}

export default function TimeAgo({ date }: TimeAgoProps) {
  return (
    <span className="text-text-secondary" title={formatDateTime(date)}>
      {formatTimeAgo(date)}
    </span>
  );
}
