import { Component, signal } from '@angular/core';
import { ChatHistoryItem } from '../chat-history-item/chat-history-item';

@Component({
  selector: 'app-sidenav',
  imports: [ChatHistoryItem],
  templateUrl: './sidenav.html',
  styleUrl: './sidenav.css',
  host: {
    '[class.collapsed]': '!open()',
  },
})
export class Sidenav {
  protected readonly chats = signal(['Project setup', 'API notes', 'Open questions']);
  protected readonly selectedIndex = signal<number | null>(null);
  protected readonly open = signal(true);

  protected select(index: number): void {
    this.selectedIndex.set(index);
  }

  protected create(): void {
    this.chats.update((chats) => ['New chat', ...chats]);
    this.selectedIndex.set(0);
  }

  protected toggle(): void {
    this.open.update((open) => !open);
  }

  protected rename(index: number, title: string): void {
    this.chats.update((chats) => chats.map((chat, i) => (i === index ? title : chat)));
  }
}
