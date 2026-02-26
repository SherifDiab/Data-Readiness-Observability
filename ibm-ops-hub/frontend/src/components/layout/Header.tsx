import { useState, useEffect } from 'react';
import { RefreshCw, Search, Wifi, WifiOff } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { format } from 'date-fns';

interface HeaderProps {
  isConnected?: boolean;
}

export default function Header({ isConnected = true }: HeaderProps) {
  const [time, setTime] = useState(new Date());
  const [search, setSearch] = useState('');
  const queryClient = useQueryClient();

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const handleRefresh = () => {
    queryClient.invalidateQueries();
  };

  return (
    <header className="h-14 bg-bg-secondary border-b border-border-color flex items-center justify-between px-6">
      <div className="flex items-center gap-4">
        <div className="relative">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-tertiary" />
          <input
            type="text"
            placeholder="Search jobs..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-bg-tertiary border border-border-color rounded-lg pl-9 pr-4 py-1.5 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:border-accent w-64"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm">
          {isConnected ? (
            <Wifi size={16} className="text-status-running" />
          ) : (
            <WifiOff size={16} className="text-status-failed" />
          )}
          <span className={isConnected ? 'text-status-running' : 'text-status-failed'}>
            {isConnected ? 'Live' : 'Disconnected'}
          </span>
        </div>

        <button
          onClick={handleRefresh}
          className="p-2 rounded-lg hover:bg-bg-hover text-text-secondary hover:text-text-primary transition-colors"
          title="Refresh all data"
        >
          <RefreshCw size={16} />
        </button>

        <div className="font-mono text-sm text-text-secondary">
          {format(time, 'HH:mm:ss')}
        </div>
      </div>
    </header>
  );
}
