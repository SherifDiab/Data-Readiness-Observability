import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { WS_URL } from '../utils/constants';

interface WSMessage {
  type: 'update' | 'alert' | 'heartbeat';
  component?: string;
  data?: unknown;
  timestamp: string;
}

export function useWebSocket() {
  const queryClient = useQueryClient();
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);
  const [isConnected, setIsConnected] = useState(false);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    try {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const msg: WSMessage = JSON.parse(event.data);

          if (msg.type === 'heartbeat') return;

          if (msg.type === 'update' && msg.component) {
            const keyMap: Record<string, string[][]> = {
              spark: [['spark', 'jobs']],
              datastage: [['datastage', 'jobs']],
              event_processing: [['event-processing', 'flows']],
              flink: [['flink', 'jobs'], ['flink', 'cluster']],
              apic: [['apic', 'logs'], ['apic', 'summary']],
            };

            const keys = keyMap[msg.component] || [];
            for (const key of keys) {
              queryClient.invalidateQueries({ queryKey: key });
            }
            queryClient.invalidateQueries({ queryKey: ['dashboard'] });
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;
        reconnectTimeoutRef.current = setTimeout(connect, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    } catch {
      // connection failed, will retry via onclose
    }
  }, [queryClient]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeoutRef.current) clearTimeout(reconnectTimeoutRef.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { isConnected };
}
