import { NormalizedJob } from './dashboard';

export interface EventProcessingFlow extends NormalizedJob {
  details: {
    jm_deployment_status?: string;
    reconciliation_status?: string;
    last_savepoint_timestamp?: string;
    parallelism?: number;
    flink_image?: string;
    [key: string]: unknown;
  };
}
