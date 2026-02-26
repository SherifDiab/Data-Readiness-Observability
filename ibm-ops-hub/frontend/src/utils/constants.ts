export const API_BASE_URL = import.meta.env.VITE_API_URL || '';
export const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`;

export const ROUTES = {
  HOME: '/',
  SPARK: '/spark',
  DATASTAGE: '/datastage',
  EVENT_PROCESSING: '/event-processing',
  FLINK: '/flink',
  APIC: '/apic',
} as const;

export const POLL_INTERVALS = {
  SPARK: 30000,
  DATASTAGE: 30000,
  FLINK: 15000,
  EVENT_PROCESSING: 30000,
  APIC: 60000,
  DASHBOARD: 30000,
} as const;

export const COMPONENT_LABELS: Record<string, string> = {
  spark: 'Spark Jobs',
  datastage: 'DataStage',
  event_processing: 'Event Processing',
  flink: 'Flink Jobs',
  apic: 'API Connect',
};
