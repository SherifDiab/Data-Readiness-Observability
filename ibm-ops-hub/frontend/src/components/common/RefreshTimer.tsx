import { useState, useEffect } from 'react';
import { Clock } from 'lucide-react';

interface RefreshTimerProps {
  intervalMs: number;
  lastUpdated?: string;
}

export default function RefreshTimer({ intervalMs, lastUpdated }: RefreshTimerProps) {
  const [countdown, setCountdown] = useState(intervalMs / 1000);

  useEffect(() => {
    setCountdown(intervalMs / 1000);
    const timer = setInterval(() => {
      setCountdown((prev) => (prev <= 1 ? intervalMs / 1000 : prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [intervalMs, lastUpdated]);

  return (
    <div className="flex items-center gap-1.5 text-xs text-text-tertiary">
      <Clock size={12} />
      <span>Refreshing in {countdown}s</span>
    </div>
  );
}
