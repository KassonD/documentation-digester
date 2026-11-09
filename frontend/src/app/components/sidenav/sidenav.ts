import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-sidenav',
  templateUrl: './sidenav.html',
  styleUrl: './sidenav.css',
  host: {
    '[class.collapsed]': '!open()',
  },
})
export class Sidenav {
  protected readonly open = signal(true);

  protected toggle(): void {
    this.open.update((open) => !open);
  }
}
