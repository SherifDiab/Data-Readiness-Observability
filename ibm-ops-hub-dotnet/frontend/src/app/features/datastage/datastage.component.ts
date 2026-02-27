import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule, DatePipe } from '@angular/common';
import { Subscription, interval } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { SignalRService } from '../../core/services/signalr.service';
import { StatusBadgeComponent } from '../../shared/status-badge/status-badge.component';
import type { NormalizedJob } from '../../core/models';

@Component({
  selector: 'app-datastage',
  standalone: true,
  imports: [CommonModule, DatePipe, StatusBadgeComponent],
  template: `
    <div class="p-6 fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-text-primary">DataStage Jobs</h1>
          <p class="text-sm text-text-secondary mt-1">ETL pipeline runs (CPD / IIS)</p>
        </div>
        <button (click)="refresh()" class="text-xs text-text-secondary hover:text-accent px-3 py-1.5 border border-border-color rounded-md hover:border-accent/50 transition-colors">
          ↻ Refresh
        </button>
      </div>
      <div class="flex gap-4 mb-4 text-xs text-text-secondary">
        <span>Total: <strong class="text-text-primary">{{ jobs.length }}</strong></span>
        <span>Running: <strong class="text-status-running">{{ count('Running') }}</strong></span>
        <span>Failed: <strong class="text-status-failed">{{ count('Failed') }}</strong></span>
        <span>Warning: <strong class="text-status-warning">{{ count('Warning') }}</strong></span>
      </div>
      <div class="bg-bg-secondary border border-border-color rounded-lg overflow-hidden">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-border-color text-xs text-text-tertiary uppercase tracking-wide">
              <th class="px-4 py-3 text-left">Name</th>
              <th class="px-4 py-3 text-left">Project / ID</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Started</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-border-color">
            @for (job of jobs; track job.id) {
              <tr class="hover:bg-bg-hover transition-colors">
                <td class="px-4 py-3 text-text-primary">{{ job.name }}</td>
                <td class="px-4 py-3 text-text-secondary font-mono text-xs">{{ job.id }}</td>
                <td class="px-4 py-3"><app-status-badge [status]="job.status" /></td>
                <td class="px-4 py-3 text-text-secondary text-xs">{{ job.started_at | date:'HH:mm:ss' }}</td>
              </tr>
            } @empty {
              <tr><td colspan="4" class="px-4 py-8 text-center text-text-tertiary">No jobs found</td></tr>
            }
          </tbody>
        </table>
      </div>
    </div>
  `,
})
export class DataStageComponent implements OnInit, OnDestroy {
  jobs: NormalizedJob[] = [];
  private subs = new Subscription();
  constructor(private api: ApiService, private signalR: SignalRService) {}
  ngOnInit(): void {
    this.load();
    this.subs.add(interval(30_000).subscribe(() => this.load()));
    this.subs.add(this.signalR.jobsUpdated$.subscribe(m => { if (m.component === 'datastage') this.jobs = m.jobs; }));
  }
  ngOnDestroy(): void { this.subs.unsubscribe(); }
  load(): void { this.api.getDataStageJobs().subscribe(j => (this.jobs = j)); }
  refresh(): void { this.api.triggerRefresh('datastage').subscribe(() => this.load()); }
  count(s: string): number { return this.jobs.filter(j => j.status === s).length; }
}
