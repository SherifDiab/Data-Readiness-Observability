import { Routes } from '@angular/router';
import { ShellComponent } from './layout/shell/shell.component';

export const routes: Routes = [
  {
    path: '',
    component: ShellComponent,
    children: [
      {
        path: '',
        loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent),
        title: 'Overview — IBM Ops Hub',
      },
      {
        path: 'spark',
        loadComponent: () => import('./features/spark/spark.component').then(m => m.SparkComponent),
        title: 'Spark Jobs — IBM Ops Hub',
      },
      {
        path: 'datastage',
        loadComponent: () => import('./features/datastage/datastage.component').then(m => m.DataStageComponent),
        title: 'DataStage — IBM Ops Hub',
      },
      {
        path: 'event-processing',
        loadComponent: () => import('./features/event-processing/event-processing.component').then(m => m.EventProcessingComponent),
        title: 'Event Processing — IBM Ops Hub',
      },
      {
        path: 'flink',
        loadComponent: () => import('./features/flink/flink.component').then(m => m.FlinkComponent),
        title: 'Flink Jobs — IBM Ops Hub',
      },
      {
        path: 'apic',
        loadComponent: () => import('./features/apic/apic.component').then(m => m.ApicComponent),
        title: 'API Connect — IBM Ops Hub',
      },
      {
        path: 'settings',
        loadComponent: () => import('./features/settings/settings.component').then(m => m.SettingsComponent),
        title: 'Settings — IBM Ops Hub',
      },
      { path: '**', redirectTo: '' },
    ],
  },
];
