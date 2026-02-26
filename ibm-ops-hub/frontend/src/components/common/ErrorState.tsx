import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
}

export default function ErrorState({
  message = 'Failed to load data',
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="bg-bg-tertiary rounded-xl border border-border-color p-8 text-center">
      <AlertTriangle size={40} className="mx-auto text-status-failed mb-3" />
      <p className="text-text-secondary mb-4">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="inline-flex items-center gap-2 px-4 py-2 bg-accent/10 text-accent rounded-lg hover:bg-accent/20 transition-colors text-sm font-medium"
        >
          <RefreshCw size={14} />
          Retry
        </button>
      )}
    </div>
  );
}
