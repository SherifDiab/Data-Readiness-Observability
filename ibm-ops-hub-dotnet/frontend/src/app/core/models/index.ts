// ── Job / Dashboard models ─────────────────────────────────────────────────
export type JobStatus =
  | 'Running' | 'Completed' | 'Failed' | 'Warning'
  | 'Unknown' | 'Queued' | 'Canceled' | 'Suspended' | 'Restarting';

export type ComponentStatus = 'Healthy' | 'Degraded' | 'Down' | 'Unknown';

export interface NormalizedJob {
  id: string;
  name: string;
  status: JobStatus;
  component: string;
  started_at?: string;
  finished_at?: string;
  duration_seconds?: number;
  details: Record<string, unknown>;
  last_polled: string;
}

export interface ComponentHealth {
  component: string;
  status: ComponentStatus;
  total_jobs: number;
  running_jobs: number;
  failed_jobs: number;
  completed_jobs: number;
  last_polled?: string;
  error_message?: string;
}

export interface DashboardSummary {
  total_jobs: number;
  running_jobs: number;
  failed_jobs: number;
  completed_jobs: number;
  healthy_components: number;
  degraded_components: number;
  recent_failures: NormalizedJob[];
  component_health_list: ComponentHealth[];
}

// ── APIC models ────────────────────────────────────────────────────────────
export interface ApiCallLog {
  id: string;
  timestamp: string;
  api_name: string;
  method: string;
  path: string;
  status_code: number;
  latency_ms: number;
  org_name: string;
  catalog_name: string;
  consumer_org: string;
  app_name: string;
}

export interface TopError {
  status_code: number;
  api_name: string;
  count: number;
}

export interface CallsByMinute {
  minute: string;
  calls: number;
  errors: number;
}

export interface ApicSummary {
  total_calls: number;
  error_calls: number;
  error_rate_percent: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  top_errors: TopError[];
  calls_by_minute: CallsByMinute[];
  timeframe: string;
}

// ── Settings models ────────────────────────────────────────────────────────
export type SettingFieldType = 'url' | 'text' | 'password' | 'boolean' | 'number' | 'tags';

export interface SettingFieldDef {
  key: string;
  label: string;
  type: SettingFieldType;
  required?: boolean;
  sensitive?: boolean;
  hint?: string;
  min?: number;
  max?: number;
}

export interface SettingsResponse {
  schema: Record<string, SettingFieldDef[]>;
  values: Record<string, unknown>;
  overrides: string[];
}

export interface SettingsUpdateResult {
  status: string;
  applied: string[];
  skipped: string[];
}

// ── SignalR message ────────────────────────────────────────────────────────
export interface JobsUpdatedMessage {
  component: string;
  jobs: NormalizedJob[];
  timestamp: string;
}
