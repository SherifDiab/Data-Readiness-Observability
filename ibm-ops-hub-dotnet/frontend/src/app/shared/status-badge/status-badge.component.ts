import { Component, Input } from '@angular/core';
import { NgClass } from '@angular/common';
import type { JobStatus } from '../../core/models';

@Component({
  selector: 'app-status-badge',
  standalone: true,
  imports: [NgClass],
  template: `
    <span class="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-medium font-mono"
      [ngClass]="badgeClass">
      <span class="w-1.5 h-1.5 rounded-full" [ngClass]="dotClass"></span>
      {{ status }}
    </span>
  `,
})
export class StatusBadgeComponent {
  @Input() status: JobStatus = 'Unknown';

  get badgeClass(): string {
    return {
      Running:    'bg-status-running/10 text-status-running',
      Completed:  'bg-status-completed/10 text-status-completed',
      Failed:     'bg-status-failed/10 text-status-failed',
      Warning:    'bg-status-warning/10 text-status-warning',
      Queued:     'bg-text-tertiary/10 text-text-tertiary',
      Canceled:   'bg-text-tertiary/10 text-text-tertiary',
      Suspended:  'bg-status-warning/10 text-status-warning',
      Restarting: 'bg-status-warning/10 text-status-warning',
      Unknown:    'bg-text-tertiary/10 text-text-tertiary',
    }[this.status] ?? 'bg-text-tertiary/10 text-text-tertiary';
  }

  get dotClass(): string {
    return {
      Running:    'bg-status-running pulse-dot',
      Completed:  'bg-status-completed',
      Failed:     'bg-status-failed',
      Warning:    'bg-status-warning',
      Restarting: 'bg-status-warning pulse-dot',
    }[this.status] ?? 'bg-text-tertiary';
  }
}
