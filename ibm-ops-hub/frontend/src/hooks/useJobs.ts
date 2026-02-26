import { useQuery } from '@tanstack/react-query';
import {
  fetchSparkJobs,
  fetchDataStageJobs,
  fetchEventProcessingFlows,
  fetchFlinkJobs,
  fetchFlinkCluster,
  fetchApicLogs,
  fetchApicSummary,
} from '../services/api';

export function useSparkJobs() {
  return useQuery({
    queryKey: ['spark', 'jobs'],
    queryFn: fetchSparkJobs,
    staleTime: Infinity,
    refetchInterval: 60000,
  });
}

export function useDataStageJobs() {
  return useQuery({
    queryKey: ['datastage', 'jobs'],
    queryFn: fetchDataStageJobs,
    staleTime: Infinity,
    refetchInterval: 60000,
  });
}

export function useEventProcessingFlows() {
  return useQuery({
    queryKey: ['event-processing', 'flows'],
    queryFn: fetchEventProcessingFlows,
    staleTime: Infinity,
    refetchInterval: 60000,
  });
}

export function useFlinkJobs() {
  return useQuery({
    queryKey: ['flink', 'jobs'],
    queryFn: fetchFlinkJobs,
    staleTime: Infinity,
    refetchInterval: 30000,
  });
}

export function useFlinkCluster() {
  return useQuery({
    queryKey: ['flink', 'cluster'],
    queryFn: fetchFlinkCluster,
    staleTime: Infinity,
    refetchInterval: 30000,
  });
}

export function useApicLogs(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['apic', 'logs', params],
    queryFn: () => fetchApicLogs(params),
    staleTime: Infinity,
    refetchInterval: 60000,
  });
}

export function useApicSummary(timeframe?: string) {
  return useQuery({
    queryKey: ['apic', 'summary', timeframe],
    queryFn: () => fetchApicSummary(timeframe),
    staleTime: Infinity,
    refetchInterval: 60000,
  });
}
