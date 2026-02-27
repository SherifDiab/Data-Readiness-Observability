import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { Subscription, interval } from 'rxjs';
import { switchMap, startWith } from 'rxjs/operators';
import { ApiService } from '../../core/services/api.service';
import { SignalRService } from '../../core/services/signalr.service';
import { StatusBadgeComponent } from '../../shared/status-badge/status-badge.component';
import type { DashboardSummary, ComponentHealth } from '../../core/models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink, StatusBadgeComponent],
  template: `
    <div class="p-6 fade-in">
      <div class="mb-6">
        <h1 class="text-2xl font-bold text-text-primary">Overview</h1>
        <p class="text-sm text-text-secondary mt-1">All IBM platform components at a glance</p>
      </div>

      <!-- Summary metrics -->
      @if (summary) {
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Total Jobs</p>
            <p class="text-3xl font-bold text-text-primary mt-1">{{ summary.total_jobs }}</p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Running</p>
            <p class="text-3xl font-bold text-status-running mt-1">{{ summary.running_jobs }}</p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Failed</p>
            <p class="text-3xl font-bold text-status-failed mt-1">{{ summary.failed_jobs }}</p>
          </div>
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
            <p class="text-xs text-text-tertiary uppercase tracking-wide">Completed</p>
            <p class="text-3xl font-bold text-status-completed mt-1">{{ summary.completed_jobs }}</p>
          </div>
        </div>

        <!-- Component health cards -->
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4 mb-6">
          @for (h of summary.component_health_list; track h.component) {
            <a [routerLink]="componentRoute(h.component)"
               class="bg-bg-secondary border border-border-color rounded-lg p-4 hover:border-accent/50 transition-colors block">
              <p class="text-xs text-text-tertiary uppercase tracking-wide mb-2">{{ componentLabel(h.component) }}</p>
              <div class="flex items-center gap-2 mb-3">
                <span class="w-2 h-2 rounded-full" [class]="healthDotClass(h.status)"></span>
                <span class="text-sm font-medium" [class]="healthTextClass(h.status)">{{ h.status }}</span>
              </div>
              <div class="text-xs text-text-secondary space-y-1">
                <div class="flex justify-between"><span>Running</span><span class="text-status-running">{{ h.running_jobs }}</span></div>
                <div class="flex justify-between"><span>Failed</span><span class="text-status-failed">{{ h.failed_jobs }}</span></div>
                <div class="flex justify-between"><span>Total</span><span>{{ h.total_jobs }}</span></div>
              </div>
            </a>
          }
        </div>

        <!-- Recent failures -->
        @if (summary.recent_failures.length > 0) {
          <div class="bg-bg-secondary border border-border-color rounded-lg">
            <div class="p-4 border-b border-border-color">
              <h2 class="text-sm font-semibold text-text-primary">Recent Failures</h2>
            </div>
            <div class="divide-y divide-border-color">
              @for (job of summary.recent_failures; track job.id) {
                <div class="px-4 py-3 flex items-center justify-between">
                  <div>
                    <p class="text-sm text-text-primary">{{ job.name }}</p>
                    <p class="text-xs text-text-tertiary font-mono">{{ job.component }} · {{ job.id }}</p>
                  </div>
                  <app-status-badge [status]="job.status" />
                </div>
              }
            </div>
          </div>
        }
      } @else {
        <div class="flex items-center justify-center h-40 text-text-secondary">
          <span class="animate-spin mr-2">⟳</span> Loading…
        </div>
      }
    </div>
  `,
})
export class DashboardComponent implements OnInit, OnDestroy {
  summary: DashboardSummary | null = null;
  private subs = new Subscription();

  constructor(private api: ApiService, private signalR: SignalRService) {}

  ngOnInit(): void {
    this.subs.add(
      interval(30_000).pipe(startWith(0), switchMap(() => this.api.getDashboardSummary()))
        .subscribe(data => (this.summary = data))
    );
    this.subs.add(
      this.signalR.jobsUpdated$.subscribe(() => {
        this.api.getDashboardSummary().subscribe(data => (this.summary = data));
      })
    );
  }

  ngOnDestroy(): void { this.subs.unsubscribe(); }

  componentLabel(c: string): string {
    return { spark: 'Spark', datastage: 'DataStage', flink: 'Flink', event_processing: 'Event Proc.', apic: 'API Connect' }[c] ?? c;
  }

  componentRoute(c: string): string {
    return { spark: '/spark', datastage: '/datastage', flink: '/flink', event_processing: '/event-processing', apic: '/apic' }[c] ?? '/';
  }

  healthDotClass(s: string): string {
    return { Healthy: 'bg-status-running', Degraded: 'bg-status-warning', Down: 'bg-status-failed', Unknown: 'bg-text-tertiary' }[s] ?? 'bg-text-tertiary';
  }

  healthTextClass(s: string): string {
    return { Healthy: 'text-status-running', Degraded: 'text-status-warning', Down: 'text-status-failed', Unknown: 'text-text-tertiary' }[s] ?? 'text-text-tertiary';
  }
}
