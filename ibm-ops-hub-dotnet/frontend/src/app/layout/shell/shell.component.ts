import { Component } from '@angular/core';
import { RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';

interface NavItem {
  path: string;
  label: string;
  icon: string; // SVG path data
  exact?: boolean;
}

@Component({
  selector: 'app-shell',
  standalone: true,
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  template: `
    <div class="flex h-screen overflow-hidden bg-bg-primary text-text-primary">

      <!-- Sidebar -->
      <aside class="w-56 bg-bg-secondary border-r border-border-color flex flex-col h-full flex-shrink-0">
        <div class="p-4 border-b border-border-color">
          <span class="text-lg font-mono font-bold text-accent">IBM Ops Hub</span>
          <p class="text-xs text-text-tertiary mt-1">Unified Monitoring (.NET)</p>
        </div>

        <nav class="flex-1 p-2 space-y-1 overflow-y-auto">
          @for (item of navItems; track item.path) {
            <a
              [routerLink]="item.path"
              [routerLinkActiveOptions]="{ exact: !!item.exact }"
              routerLinkActive="bg-accent/10 text-accent"
              class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-colors"
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path [attr.d]="item.icon" />
              </svg>
              {{ item.label }}
            </a>
          }
        </nav>

        <div class="p-2 border-t border-border-color">
          <a
            routerLink="/settings"
            routerLinkActive="bg-accent/10 text-accent"
            class="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-text-secondary hover:bg-bg-hover hover:text-text-primary transition-colors"
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z M12 15A3 3 0 1 0 12 9a3 3 0 0 0 0 6z"/>
            </svg>
            Settings
          </a>
          <p class="text-xs text-text-tertiary px-3 pt-2">v2.0.0</p>
        </div>
      </aside>

      <!-- Main content -->
      <main class="flex-1 overflow-y-auto">
        <router-outlet />
      </main>
    </div>
  `,
})
export class ShellComponent {
  navItems: NavItem[] = [
    { path: '', label: 'Overview', exact: true, icon: 'M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z M9 22V12h6v10' },
    { path: 'spark', label: 'Spark Jobs', icon: 'M13 2L3 14h9l-1 8 10-12h-9l1-8z' },
    { path: 'datastage', label: 'DataStage', icon: 'M22 12H2 M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z M6 16h.01 M10 16h.01' },
    { path: 'event-processing', label: 'Event Processing', icon: 'M1 6C1 6 5 2 12 2s11 4 11 4 M1 18s4 4 11 4 11-4 11-4 M12 12a1 1 0 1 0 0-2 1 1 0 0 0 0 2z' },
    { path: 'flink', label: 'Flink Jobs', icon: 'M22 12h-4l-3 9L9 3l-3 9H2' },
    { path: 'apic', label: 'API Connect', icon: 'M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z M2 12h20 M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' },
  ];
}
