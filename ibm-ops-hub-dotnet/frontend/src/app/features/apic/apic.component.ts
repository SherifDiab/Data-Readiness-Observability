import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Subscription, interval } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import type { ApicSummary, ApiCallLog } from '../../core/models';

@Component({
  selector: 'app-apic',
  standalone: true,
  imports: [CommonModule, DatePipe],
  template: `
    <div class="p-6 fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-text-primary">API Connect</h1>
          <p class="text-sm text-text-secondary mt-1">Analytics and call logs for the last hour</p>
        </div>
        <button (click)="load()" class="text-xs text-text-secondary hover:text-accent px-3 py-1.5 border border-border-color rounded-md hover:border-accent/50 transition-colors">
          ↻ Refresh
        </button>
      </div>

      @if (summary) {
        <!-- Metric cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Total Calls</p>
            <p class="text-3xl font-bold text-text-primary mt-1">{{ summary.total_calls }}</p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Error Rate</p>
            <p class="text-3xl font-bold mt-1" [class]="summary.error_rate_percent > 5 ? 'text-status-failed' : 'text-status-running'">
              {{ summary.error_rate_percent | number:'1.1-1' }}%
            </p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Avg Latency</p>
            <p class="text-3xl font-bold text-text-primary mt-1">{{ summary.avg_latency_ms | number:'1.0-0' }}<span class="text-sm ml-1 text-text-secondary">ms</span></p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">P95 Latency</p>
            <p class="text-3xl font-bold text-text-primary mt-1">{{ summary.p95_latency_ms | number:'1.0-0' }}<span class="text-sm ml-1 text-text-secondary">ms</span></p>
          </div>
        </div>

        <!-- Calls per minute chart (simple bars) -->
        <div class="bg-bg-secondary border border-border-color rounded-lg p-4 mb-6">
          <h2 class="text-sm font-semibold text-text-primary mb-4">Calls per Minute</h2>
          <div class="flex items-end gap-0.5 h-24 overflow-x-auto">
            @for (b of summary.calls_by_minute; track b.minute) {
              <div class="flex-1 min-w-[6px] flex flex-col justify-end gap-0.5" [title]="b.minute | date:'HH:mm' ">
                <div class="bg-status-failed/70 rounded-sm" [style.height.px]="barPx(b.errors, maxCalls)"></div>
                <div class="bg-accent/50 rounded-sm" [style.height.px]="barPx(b.calls - b.errors, maxCalls)"></div>
              </div>
            }
          </div>
          <div class="flex gap-4 mt-2 text-xs text-text-tertiary">
            <span class="flex items-center gap-1"><span class="w-3 h-2 bg-accent/50 rounded-sm inline-block"></span> OK</span>
            <span class="flex items-center gap-1"><span class="w-3 h-2 bg-status-failed/70 rounded-sm inline-block"></span> Errors</span>
          </div>
        </div>

        <!-- Top errors -->
        @if (summary.top_errors.length) {
          <div class="bg-bg-secondary border border-border-color rounded-lg mb-6">
            <div class="p-4 border-b border-border-color">
              <h2 class="text-sm font-semibold text-text-primary">Top Errors</h2>
            </div>
            <div class="divide-y divide-border-color">
              @for (e of summary.top_errors; track $index) {
                <div class="px-4 py-3 flex items-center justify-between">
                  <div class="flex items-center gap-3">
                    <span class="text-xs font-mono px-2 py-0.5 rounded" [class]="e.status_code >= 500 ? 'bg-status-failed/10 text-status-failed' : 'bg-status-warning/10 text-status-warning'">
                      {{ e.status_code }}
                    </span>
                    <span class="text-sm text-text-primary">{{ e.api_name }}</span>
                  </div>
                  <span class="text-sm font-bold text-text-secondary">{{ e.count }}</span>
                </div>
              }
            </div>
          </div>
        }
      }

      <!-- Recent log entries -->
      <div class="bg-bg-secondary border border-border-color rounded-lg overflow-hidden">
        <div class="p-4 border-b border-border-color">
          <h2 class="text-sm font-semibold text-text-primary">Recent API Calls</h2>
        </div>
        <table class="w-full text-xs">
          <thead>
            <tr class="border-b border-border-color text-text-tertiary uppercase tracking-wide">
              <th class="px-4 py-2 text-left">Time</th>
              <th class="px-4 py-2 text-left">API</th>
              <th class="px-4 py-2 text-left">Method</th>
              <th class="px-4 py-2 text-left">Status</th>
              <th class="px-4 py-2 text-left">Latency</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border-color font-mono">
            @for (log of logs.slice(0, 50); track log.id) {
              <tr class="hover:bg-bg-hover transition-colors">
                <td class="px-4 py-2 text-text-tertiary">{{ log.timestamp | date:'HH:mm:ss' }}</td>
                <td class="px-4 py-2 text-text-primary">{{ log.api_name }}</td>
                <td class="px-4 py-2 text-text-secondary">{{ log.method }}</td>
                <td class="px-4 py-2">
                  <span [class]="log.status_code >= 400 ? 'text-status-failed' : 'text-status-running'">{{ log.status_code }}</span>
                </td>
                <td class="px-4 py-2 text-text-secondary">{{ log.latency_ms | number:'1.0-0' }}ms</td>
              </tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class ApicComponent implements OnInit, OnDestroy {
  summary: ApicSummary | null = null;
  logs: ApiCallLog[] = [];
  maxCalls = 1;
  private subs = new Subscription();

  constructor(private api: ApiService) {}

  ngOnInit(): void {
    this.load();
    this.subs.add(interval(60_000).subscribe(() => this.load()));
  }

  ngOnDestroy(): void { this.subs.unsubscribe(); }

  load(): void {
    this.api.getApicSummary().subscribe(s => {
      this.summary = s;
      this.maxCalls = Math.max(...s.calls_by_minute.map(b => b.calls), 1);
    });
    this.api.getApicLogs().subscribe(l => (this.logs = l.sort((a, b) => b.timestamp.localeCompare(a.timestamp))));
  }

  barPx(val: number, max: number): number {
    return Math.max(2, Math.round((val / max) * 80));
  }
}
