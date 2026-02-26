import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';
import type { NormalizedJob, DashboardSummary, ComponentHealth } from '../types/dashboard';
import type { FlinkClusterOverview } from '../types/flink';
import type { ApiCallLog, ApicSummary } from '../types/apic';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
});

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await api.get('/api/dashboard/summary');
  return data;
}

export async function fetchDashboardHealth(): Promise<ComponentHealth[]> {
  const { data } = await api.get('/api/dashboard/health');
  return data;
}

export async function fetchSparkJobs(): Promise<NormalizedJob[]> {
  const { data } = await api.get('/api/spark/jobs');
  return data;
}

export async function fetchDataStageJobs(): Promise<NormalizedJob[]> {
  const { data } = await api.get('/api/datastage/jobs');
  return data;
}

export async function fetchEventProcessingFlows(): Promise<NormalizedJob[]> {
  const { data } = await api.get('/api/event-processing/flows');
  return data;
}

export async function fetchFlinkJobs(): Promise<NormalizedJob[]> {
  const { data } = await api.get('/api/flink/jobs');
  return data;
}

export async function fetchFlinkCluster(): Promise<FlinkClusterOverview> {
  const { data } = await api.get('/api/flink/cluster');
  return data;
}

export async function fetchApicLogs(params?: Record<string, string>): Promise<ApiCallLog[]> {
  const { data } = await api.get('/api/apic/logs', { params });
  return data;
}

export async function fetchApicSummary(timeframe?: string): Promise<ApicSummary> {
  const { data } = await api.get('/api/apic/summary', { params: timeframe ? { timeframe } : {} });
  return data;
}

export async function refreshComponent(component: string): Promise<void> {
  await api.post(`/api/settings/refresh/${component}`);
}

export default api;
