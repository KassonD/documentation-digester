import { Component } from '@angular/core';
import { Dashboard } from './components/dashboard/dashboard';
import { Sidenav } from './components/sidenav/sidenav';

@Component({
  selector: 'app-root',
  imports: [Dashboard, Sidenav],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App {}
