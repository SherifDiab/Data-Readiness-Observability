export interface ApiCallLog {
  timestamp: string;
  api_name: string;
  path: string;
  method: string;
  status_code: number;
  latency_ms: number;
  client_ip: string | null;
  consumer_org: string | null;
}

export interface ApicSummary {
  total_calls: number;
  success_count: number;
  error_count: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  error_rate_percent: number;
  top_errors: Array<{ status_code: number; api: string; count: number }>;
  calls_by_minute: Array<{ minute: string; count: number }>;
  timeframe: string;
}
