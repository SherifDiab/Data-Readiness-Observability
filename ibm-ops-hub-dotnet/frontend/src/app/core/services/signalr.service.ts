import { Injectable } from '@angular/core';
import { Subject } from 'rxjs';
import * as signalR from '@microsoft/signalr';
import type { JobsUpdatedMessage } from '../models';

@Injectable({ providedIn: 'root' })
export class SignalRService {
  private hub!: signalR.HubConnection;

  /** Emits whenever the server pushes a JobsUpdated event. */
  readonly jobsUpdated$ = new Subject<JobsUpdatedMessage>();

  connect(url: string): void {
    this.hub = new signalR.HubConnectionBuilder()
      .withUrl(url)
      .withAutomaticReconnect([1000, 2000, 4000, 8000, 16000, 30000])
      .configureLogging(signalR.LogLevel.Warning)
      .build();

    this.hub.on('JobsUpdated', (msg: JobsUpdatedMessage) => {
      this.jobsUpdated$.next(msg);
    });

    this.hub
      .start()
      .then(() => console.log('SignalR connected'))
      .catch(err => console.error('SignalR connection error:', err));

    this.hub.onreconnected(() => console.log('SignalR reconnected'));
    this.hub.onclose(() => console.warn('SignalR connection closed'));
  }

  subscribe(component: string): void {
    if (this.hub.state === signalR.HubConnectionState.Connected)
      this.hub.invoke('Subscribe', component).catch(console.error);
  }
}
