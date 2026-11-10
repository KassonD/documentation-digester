import { Component, input, signal } from '@angular/core';

@Component({
  selector: 'app-copy-badge',
  imports: [],
  templateUrl: './copy-badge.html',
  styleUrl: './copy-badge.css'
})
export class CopyBadge {
  message = input.required<string>();

  copied = signal(false);

  async copyMessage() {
    try {
      await navigator.clipboard.writeText(this.message());

      this.copied.set(true);

      setTimeout(() => {
        this.copied.set(false);
      }, 2000);

    } catch (error) {
      console.error('Failed to copy message:', error);
    }
  }
}