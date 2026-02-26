import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { format, parseISO } from 'date-fns';

interface ErrorRateChartProps {
  data: Array<{ minute: string; rate: number }>;
}

export default function ErrorRateChart({ data }: ErrorRateChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    label: (() => { try { return format(parseISO(d.minute), 'HH:mm'); } catch { return d.minute; } })(),
  }));

  return (
    <ResponsiveContainer width="100%" height={160}>
      <LineChart data={formatted} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#2a3a50" />
        <XAxis dataKey="label" tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} />
        <YAxis tick={{ fill: '#64748b', fontSize: 10 }} tickLine={false} axisLine={false} width={40}
          tickFormatter={(v) => `${v}%`} />
        <Tooltip
          contentStyle={{ background: '#111827', border: '1px solid #2a3a50', borderRadius: 8, fontSize: 12 }}
          labelStyle={{ color: '#94a3b8' }}
          itemStyle={{ color: '#ef4444' }}
          formatter={(v: number) => [`${v.toFixed(1)}%`, 'Error Rate']}
        />
        <Line type="monotone" dataKey="rate" stroke="#ef4444" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
