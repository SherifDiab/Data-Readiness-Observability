import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Zap, Database, Radio, Activity, Globe } from 'lucide-react';
import clsx from 'clsx';
import { ROUTES } from '../../utils/constants';

const navItems = [
  { to: ROUTES.HOME, label: 'Overview', icon: LayoutDashboard },
  { to: ROUTES.SPARK, label: 'Spark Jobs', icon: Zap },
  { to: ROUTES.DATASTAGE, label: 'DataStage', icon: Database },
  { to: ROUTES.EVENT_PROCESSING, label: 'Event Processing', icon: Radio },
  { to: ROUTES.FLINK, label: 'Flink Jobs', icon: Activity },
  { to: ROUTES.APIC, label: 'API Connect', icon: Globe },
];

export default function Sidebar() {
  return (
    <aside className="w-56 bg-bg-secondary border-r border-border-color flex flex-col h-full">
      <div className="p-4 border-b border-border-color">
        <h1 className="text-lg font-mono font-bold text-accent">IBM Ops Hub</h1>
        <p className="text-xs text-text-tertiary mt-1">Unified Monitoring</p>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              clsx(
                'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                isActive
                  ? 'bg-accent/10 text-accent'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary'
              )
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-border-color">
        <p className="text-xs text-text-tertiary">v1.0.0</p>
      </div>
    </aside>
  );
}
