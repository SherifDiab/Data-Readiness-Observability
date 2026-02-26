export type JobStatus =
  | 'Running'
  | 'Completed'
  | 'Failed'
  | 'Canceled'
  | 'Queued'
  | 'Starting'
  | 'Warning'
  | 'Suspended'
  | 'Restarting'
  | 'Unknown';

export type ComponentType =
  | 'spark'
  | 'datastage'
  | 'event_processing'
  | 'flink'
  | 'apic';

export interface NormalizedJob {
  component: ComponentType;
  job_id: string;
  job_name: string;
  status: JobStatus;
  started_at: string | null;
  finished_at: string | null;
  duration_seconds: number | null;
  details: Record<string, unknown>;
  native_url: string | null;
  last_polled_at: string;
}

export interface ComponentHealth {
  component: ComponentType;
  total_jobs: number;
  running: number;
  completed: number;
  failed: number;
  warning: number;
  other: number;
  last_polled_at: string;
  is_reachable: boolean;
  error_message: string | null;
}

export interface DashboardSummary {
  components: ComponentHealth[];
  total_failures: number;
  critical_alerts: string[];
  last_updated: string;
}
