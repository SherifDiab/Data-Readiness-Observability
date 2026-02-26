import { ReactNode } from 'react';
import clsx from 'clsx';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon?: ReactNode;
  trend?: 'up' | 'down' | 'neutral';
  className?: string;
}

export default function MetricCard({ title, value, subtitle, icon, className }: MetricCardProps) {
  return (
    <div className={clsx('bg-bg-tertiary rounded-xl border border-border-color p-4', className)}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-text-secondary font-medium">{title}</span>
        {icon && <span className="text-text-tertiary">{icon}</span>}
      </div>
      <div className="text-2xl font-mono font-bold text-text-primary">{value}</div>
      {subtitle && <p className="text-xs text-text-tertiary mt-1">{subtitle}</p>}
    </div>
  );
}
