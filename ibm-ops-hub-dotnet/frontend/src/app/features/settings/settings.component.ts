import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../core/services/api.service';
import type { SettingsResponse, SettingFieldDef } from '../../core/models';

const CATEGORY_LABELS: Record<string, string> = {
  cpd: 'CPD Connection',
  datastage: 'DataStage',
  flink: 'Flink',
  event_processing: 'Event Processing',
  apic: 'API Connect',
  polling: 'Polling Intervals',
  general: 'General',
};

const PLACEHOLDER = '••••••••';

type Feedback = { type: 'success' | 'error'; message: string } | null;

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
    <div class="p-6 max-w-4xl mx-auto fade-in">
      <!-- Header -->
      <div class="flex items-start justify-between mb-6">
        <div>
          <h1 class="text-2xl font-bold text-text-primary">Settings</h1>
          <p class="text-sm text-text-secondary mt-1">Configure IBM Ops Hub connections and polling intervals. Changes take effect immediately.</p>
        </div>
        <button (click)="save()" [disabled]="saving"
          class="flex items-center gap-2 px-4 py-2 bg-accent text-bg-primary rounded-lg hover:bg-accent/90 disabled:opacity-50 transition-colors text-sm font-medium">
          {{ saving ? 'Saving…' : '✓ Save Changes' }}
        </button>
      </div>

      <!-- Feedback -->
      @if (feedback) {
        <div class="flex items-center gap-3 p-3 rounded-lg border mb-5"
          [class]="feedback.type === 'success'
            ? 'bg-status-running/10 border-status-running/30 text-status-running'
            : 'bg-status-failed/10 border-status-failed/30 text-status-failed'">
          <span class="flex-1 text-sm">{{ feedback.message }}</span>
          <button (click)="feedback = null" class="opacity-60 hover:opacity-100">✕</button>
        </div>
      }

      @if (isLoading) {
        <div class="flex items-center justify-center h-40 text-text-secondary">Loading…</div>
      } @else if (data) {
        <!-- Tabs -->
        <div class="flex gap-0 border-b border-border-color mb-6 overflow-x-auto">
          @for (cat of categories; track cat) {
            <button (click)="activeTab = cat"
              class="px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 -mb-px"
              [class]="activeTab === cat
                ? 'border-accent text-accent'
                : 'border-transparent text-text-secondary hover:text-text-primary'">
              {{ label(cat) }}
            </button>
          }
        </div>

        <!-- Fields for active tab -->
        @for (cat of categories; track cat) {
          @if (cat === activeTab) {
            <div class="space-y-4">
              <!-- Force re-poll button for service categories -->
              @if (['spark','datastage','flink','event_processing','apic'].includes(cat)) {
                <div class="flex justify-end">
                  <button (click)="triggerRefresh(cat)" [disabled]="refreshing === cat"
                    class="text-xs text-text-secondary hover:text-accent px-3 py-1.5 border border-border-color rounded-md hover:border-accent/50 transition-colors">
                    {{ refreshing === cat ? 'Triggering…' : '↻ Force re-poll now' }}
                  </button>
                </div>
              }

              @for (field of data.schema[cat]; track field.key) {
                <div class="bg-bg-secondary border border-border-color rounded-lg p-4">
                  <div class="flex items-center gap-2 mb-1">
                    <label class="text-sm font-medium text-text-primary">
                      {{ field.label }}
                      @if (field.required) { <span class="text-status-failed ml-1">*</span> }
                    </label>
                    @if (data.overrides.includes(field.key)) {
                      <span class="text-xs bg-accent/10 text-accent px-1.5 py-0.5 rounded font-mono">overridden</span>
                    }
                    <span class="text-xs text-text-tertiary font-mono ml-auto">{{ field.key }}</span>
                  </div>
                  @if (field.hint) {
                    <p class="text-xs text-text-tertiary mb-3">{{ field.hint }}</p>
                  }

                  <!-- Boolean toggle -->
                  @if (field.type === 'boolean') {
                    <div class="flex items-center gap-3">
                      <button type="button" (click)="toggleBool(field.key)"
                        class="relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-1"
                        [class]="values[field.key] ? 'bg-accent' : 'bg-bg-hover'">
                        <span class="inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform"
                          [class]="values[field.key] ? 'translate-x-6' : 'translate-x-1'"></span>
                      </button>
                      <span class="text-sm text-text-secondary">{{ values[field.key] ? 'Enabled' : 'Disabled' }}</span>
                    </div>

                  <!-- Tags input -->
                  } @else if (field.type === 'tags') {
                    <div class="space-y-2">
                      @if (tagsFor(field.key).length) {
                        <div class="flex flex-wrap gap-2">
                          @for (tag of tagsFor(field.key); track tag) {
                            <span class="flex items-center gap-1.5 bg-accent/10 text-accent text-xs px-2.5 py-1 rounded-md font-mono">
                              {{ tag }}
                              <button type="button" (click)="removeTag(field.key, tag)" class="hover:text-accent/60">✕</button>
                            </span>
                          }
                        </div>
                      }
                      <div class="flex gap-2">
                        <input type="text" [(ngModel)]="tagInputs[field.key]"
                          (keydown.enter)="addTag(field.key, $event)"
                          (keydown.comma)="addTag(field.key, $event)"
                          placeholder="Type a project ID and press Enter"
                          class="flex-1 bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent font-mono" />
                        <button type="button" (click)="addTagClick(field.key)"
                          class="px-3 py-1.5 bg-accent/10 text-accent rounded-md text-sm hover:bg-accent/20 transition-colors font-medium">Add</button>
                      </div>
                    </div>

                  <!-- Number input -->
                  } @else if (field.type === 'number') {
                    <div class="flex items-center gap-3">
                      <input type="number" [(ngModel)]="values[field.key]"
                        [min]="field.min" [max]="field.max"
                        class="w-36 bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent" />
                      @if (field.min !== undefined && field.max !== undefined) {
                        <span class="text-xs text-text-tertiary">{{ field.min }}–{{ field.max }} seconds</span>
                      }
                    </div>

                  <!-- Text / URL / Password -->
                  } @else {
                    <input [type]="field.type === 'password' ? 'password' : field.type === 'url' ? 'url' : 'text'"
                      [(ngModel)]="values[field.key]"
                      [placeholder]="field.type === 'password' && values[field.key] === placeholder ? 'Enter new value to change' : field.type === 'url' ? 'https://…' : ''"
                      [autocomplete]="field.type === 'password' ? 'new-password' : 'off'"
                      class="w-full bg-bg-primary border border-border-color rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-1 focus:ring-accent focus:border-accent font-mono" />
                  }
                </div>
              }
            </div>
          }
        }
      }
    </div>
  `,
})
export class SettingsComponent implements OnInit {
  data: SettingsResponse | null = null;
  values: Record<string, unknown> = {};
  tagInputs: Record<string, string> = {};
  categories: string[] = [];
  activeTab = '';
  isLoading = true;
  saving = false;
  refreshing: string | null = null;
  feedback: Feedback = null;
  readonly placeholder = PLACEHOLDER;

  constructor(private api: ApiService) {}

  ngOnInit(): void { this.loadSettings(); }

  loadSettings(): void {
    this.isLoading = true;
    this.api.getSettings().subscribe({
      next: d => {
        this.data = d;
        this.values = { ...d.values };
        this.categories = Object.keys(d.schema);
        if (!this.activeTab && this.categories.length) this.activeTab = this.categories[0];
        this.isLoading = false;
      },
      error: () => { this.feedback = { type: 'error', message: 'Failed to load settings.' }; this.isLoading = false; }
    });
  }

  save(): void {
    this.saving = true;
    const changes: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(this.values)) {
      if (v === PLACEHOLDER) continue;
      changes[k] = v;
    }
    this.api.updateSettings(changes).subscribe({
      next: r => {
        const msg = r.applied.length ? `Saved: ${r.applied.join(', ')}` : 'No changes applied.';
        this.feedback = { type: 'success', message: msg };
        this.saving = false;
        this.loadSettings();
      },
      error: () => { this.feedback = { type: 'error', message: 'Save failed.' }; this.saving = false; }
    });
  }

  triggerRefresh(component: string): void {
    this.refreshing = component;
    this.api.triggerRefresh(component).subscribe({
      next: () => { this.feedback = { type: 'success', message: `Triggered re-poll for ${component}.` }; this.refreshing = null; },
      error: () => { this.feedback = { type: 'error', message: 'Refresh failed.' }; this.refreshing = null; }
    });
  }

  label(cat: string): string { return CATEGORY_LABELS[cat] ?? cat; }

  toggleBool(key: string): void { this.values[key] = !this.values[key]; }

  tagsFor(key: string): string[] {
    const v = this.values[key];
    return v ? String(v).split(',').map(t => t.trim()).filter(Boolean) : [];
  }

  addTag(key: string, event: Event): void {
    event.preventDefault();
    this.addTagClick(key);
  }

  addTagClick(key: string): void {
    const input = (this.tagInputs[key] ?? '').trim().replace(/,/g, '');
    if (!input) return;
    const existing = this.tagsFor(key);
    if (!existing.includes(input)) {
      this.values[key] = [...existing, input].join(',');
    }
    this.tagInputs[key] = '';
  }

  removeTag(key: string, tag: string): void {
    this.values[key] = this.tagsFor(key).filter(t => t !== tag).join(',');
  }
}
