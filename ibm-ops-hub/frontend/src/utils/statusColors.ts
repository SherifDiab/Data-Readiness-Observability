import { JobStatus } from '../types/dashboard';

export const statusColors: Record<JobStatus, string> = {
  Running: 'bg-status-running/20 text-status-running border-status-running',
  Completed: 'bg-status-completed/20 text-status-completed border-status-completed',
  Failed: 'bg-status-failed/20 text-status-failed border-status-failed',
  Canceled: 'bg-status-canceled/20 text-status-canceled border-status-canceled',
  Queued: 'bg-status-queued/20 text-status-queued border-status-queued',
  Starting: 'bg-status-queued/20 text-status-queued border-status-queued',
  Warning: 'bg-status-warning/20 text-status-warning border-status-warning',
  Suspended: 'bg-status-suspended/20 text-status-suspended border-status-suspended',
  Restarting: 'bg-status-warning/20 text-status-warning border-status-warning',
  Unknown: 'bg-status-canceled/20 text-status-canceled border-status-canceled',
};

export const statusDotColors: Record<JobStatus, string> = {
  Running: 'bg-status-running',
  Completed: 'bg-status-completed',
  Failed: 'bg-status-failed',
  Canceled: 'bg-status-canceled',
  Queued: 'bg-status-queued',
  Starting: 'bg-status-queued',
  Warning: 'bg-status-warning',
  Suspended: 'bg-status-suspended',
  Restarting: 'bg-status-warning',
  Unknown: 'bg-status-canceled',
};
