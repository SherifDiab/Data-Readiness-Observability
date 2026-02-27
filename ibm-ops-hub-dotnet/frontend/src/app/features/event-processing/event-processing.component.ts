import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Subscription, interval } from 'rxjs';
import { ApiService } from '../../core/services/api.service';
import { SignalRService } from '../../core/services/signalr.service';
import { StatusBadgeComponent } from '../../shared/status-badge/status-badge.component';
import type { NormalizedJob } from '../../core/models';

@Component({
  selector: 'app-event-processing',
  standalone: true,
  imports: [CommonModule, StatusBadgeComponent],
  template: `
    <div class="p-6 fade-in">
      <div class="flex items-center justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-text-primary">Event Processing Flows</h1>
          <p class="text-sm text-text-secondary mt-1">IBM Event Automation FlinkDeployment CRDs</p>
        </div>
        <button (click)="refresh()" class="text-xs text-text-secondary hover:text-accent px-3 py-1.5 border border-border-color rounded-md hover:border-accent/50 transition-colors">
          ↻ Refresh
        </button>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        @for (flow of flows; track flow.id) {
          <div class="bg-bg-secondary border border-border-color rounded-lg p-4 hover:border-accent/30 transition-colors">
            <div class="flex items-start justify-between mb-3">
              <div>
                <p class="text-sm font-medium text-text-primary">{{ flow.name }}</p>
                <p class="text-xs text-text-tertiary font-mono mt-0.5">{{ flow.details['namespace'] }}</p>
              </div>
              <app-status-badge [status]="flow.status" />
            </div>
            <div class="text-xs text-text-secondary space-y-1">
              <div class="flex justify-between">
                <span>Lifecycle</span>
                <span class="font-mono">{{ flow.details['lifecycle_state'] }}</span>
              </div>
              <div class="flex justify-between">
                <span>Job state</span>
                <span class="font-mono">{{ flow.details['job_state'] || '—' }}</span>
              </div>
            </div>
          </div>
        } @empty {
          <div class="col-span-3 text-center text-text-tertiary py-12">No event flows found</div>
        }
      </div>
    </div>
  `,
})
export class EventProcessingComponent implements OnInit, OnDestroy {
  flows: NormalizedJob[] = [];
  private subs = new Subscription();
  constructor(private api: ApiService, private signalR: SignalRService) {}
  ngOnInit(): void {
    this.load();
    this.subs.add(interval(30_000).subscribe(() => this.load()));
    this.subs.add(this.signalR.jobsUpdated$.subscribe(m => { if (m.component === 'event_processing') this.flows = m.jobs; }));
  }
  ngOnDestroy(): void { this.subs.unsubscribe(); }
  load(): void { this.api.getEventProcessingFlows().subscribe(f => (this.flows = f)); }
  refresh(): void { this.api.triggerRefresh('event_processing').subscribe(() => this.load()); }
}
