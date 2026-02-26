import { NormalizedJob } from './dashboard';

export interface FlinkJob extends NormalizedJob {
  details: {
    tasks?: {
      total: number;
      running: number;
      finished: number;
      failed: number;
      [key: string]: number;
    };
    root_exception?: string;
    last_checkpoint?: string;
    [key: string]: unknown;
  };
}

export interface FlinkClusterOverview {
  taskmanagers: number;
  slots_total: number;
  slots_available: number;
  jobs_running: number;
  jobs_finished: number;
  jobs_cancelled: number;
  jobs_failed: number;
  flink_version: string;
}
