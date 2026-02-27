import { Component, OnInit } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SignalRService } from './core/services/signalr.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [RouterOutlet],
  template: '<router-outlet />',
})
export class AppComponent implements OnInit {
  constructor(private signalR: SignalRService) {}

  ngOnInit(): void {
    this.signalR.connect('/hubs/ops');
  }
}
