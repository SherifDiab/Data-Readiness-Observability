import { AlertTriangle } from 'lucide-react';

interface AlertBannerProps {
  alerts: string[];
}

export default function AlertBanner({ alerts }: AlertBannerProps) {
  if (!alerts || alerts.length === 0) return null;

  return (
    <div className="bg-status-failed/10 border border-status-failed rounded-xl p-4">
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle size={18} className="text-status-failed" />
        <span className="text-sm font-medium text-status-failed">
          {alerts.length} Critical Alert{alerts.length > 1 ? 's' : ''}
        </span>
      </div>
      <ul className="space-y-1">
        {alerts.map((alert, i) => (
          <li key={i} className="text-sm text-text-secondary flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-status-failed flex-shrink-0" />
            {alert}
          </li>
        ))}
      </ul>
    </div>
  );
}
