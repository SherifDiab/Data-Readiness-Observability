import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import type {
  NormalizedJob, DashboardSummary, ComponentHealth,
  ApiCallLog, ApicSummary, SettingsResponse, SettingsUpdateResult
} from '../models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api';

  // ── Dashboard ──────────────────────────────────────────────────────────
  getDashboardSummary(): Observable<DashboardSummary> {
    return this.http.get<DashboardSummary>(`${this.base}/dashboard/summary`);
  }

  getDashboardHealth(): Observable<ComponentHealth[]> {
    return this.http.get<ComponentHealth[]>(`${this.base}/dashboard/health`);
  }

  // ── Component jobs ────────────────────────────────────────────────────
  getSparkJobs(): Observable<NormalizedJob[]> {
    return this.http.get<NormalizedJob[]>(`${this.base}/spark/jobs`);
  }

  getDataStageJobs(): Observable<NormalizedJob[]> {
    return this.http.get<NormalizedJob[]>(`${this.base}/datastage/jobs`);
  }

  getEventProcessingFlows(): Observable<NormalizedJob[]> {
    return this.http.get<NormalizedJob[]>(`${this.base}/event-processing/flows`);
  }

  getFlinkJobs(): Observable<NormalizedJob[]> {
    return this.http.get<NormalizedJob[]>(`${this.base}/flink/jobs`);
  }

  // ── APIC ──────────────────────────────────────────────────────────────
  getApicLogs(filters?: { apiName?: string; statusCode?: string }): Observable<ApiCallLog[]> {
    let params = new HttpParams();
    if (filters?.apiName) params = params.set('apiName', filters.apiName);
    if (filters?.statusCode) params = params.set('statusCode', filters.statusCode);
    return this.http.get<ApiCallLog[]>(`${this.base}/apic/logs`, { params });
  }

  getApicSummary(timeframe = '1h'): Observable<ApicSummary> {
    return this.http.get<ApicSummary>(`${this.base}/apic/summary`, {
      params: new HttpParams().set('timeframe', timeframe),
    });
  }

  // ── Settings ──────────────────────────────────────────────────────────
  getSettings(): Observable<SettingsResponse> {
    return this.http.get<SettingsResponse>(`${this.base}/settings`);
  }

  updateSettings(changes: Record<string, unknown>): Observable<SettingsUpdateResult> {
    return this.http.put<SettingsUpdateResult>(`${this.base}/settings`, { changes });
  }

  triggerRefresh(component: string): Observable<unknown> {
    return this.http.post(`${this.base}/settings/refresh/${component}`, {});
  }
}
