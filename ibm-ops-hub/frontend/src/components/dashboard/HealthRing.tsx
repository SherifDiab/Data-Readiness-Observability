import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';

interface HealthRingProps {
  running: number;
  completed: number;
  failed: number;
  warning: number;
  other: number;
  label: string;
}

export default function HealthRing({ running, completed, failed, warning, other }: HealthRingProps) {
  const total = running + completed + failed + warning + other;
  const data = [
    { name: 'Running', value: running, color: '#22c55e' },
    { name: 'Completed', value: completed, color: '#3b82f6' },
    { name: 'Failed', value: failed, color: '#ef4444' },
    { name: 'Warning', value: warning, color: '#f59e0b' },
    { name: 'Other', value: other, color: '#6b7280' },
  ].filter((d) => d.value > 0);

  if (total === 0) {
    return (
      <div className="h-24 flex items-center justify-center text-text-tertiary text-xs">
        No jobs
      </div>
    );
  }

  return (
    <div className="relative h-24">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={28}
            outerRadius={40}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
        </PieChart>
      </ResponsiveContainer>
      <div className="absolute inset-0 flex items-center justify-center">
        <span className="font-mono text-sm font-bold text-text-primary">{total}</span>
      </div>
    </div>
  );
}
