import { NormalizedJob } from './dashboard';

export interface DataStageJob extends NormalizedJob {
  details: {
    rows_read?: number;
    rows_written?: number;
    warnings_count?: number;
    project_name?: string;
    flow_name?: string;
    [key: string]: unknown;
  };
}
