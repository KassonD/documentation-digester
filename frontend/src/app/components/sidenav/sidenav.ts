import { Component, ElementRef, inject, signal } from '@angular/core';
import { ChatHistoryItem } from '../chat-history-item/chat-history-item';

interface Chat {
  id: number;
  title: string;
}

@Component({
  selector: 'app-sidenav',
  imports: [ChatHistoryItem],
  templateUrl: './sidenav.html',
  styleUrl: './sidenav.css',
  host: {
    '[class.collapsed]': '!open()',
    '[class.animating]': 'animating()',
  },
})
export class Sidenav {
  private readonly host = inject(ElementRef<HTMLElement>);
  private animationTimer?: ReturnType<typeof setTimeout>;
  private nextId = 3;

  protected readonly chats = signal<Chat[]>([
    { id: 0, title: 'Project setup' },
    { id: 1, title: 'API notes' },
    { id: 2, title: 'Open questions' },
  ]);
  protected readonly selectedId = signal<number | null>(null);
  protected readonly open = signal(true);
  protected readonly animating = signal(false);

  protected select(id: number): void {
    this.selectedId.set(id);
  }

  protected create(): void {
    const id = this.nextId++;
    this.chats.update((chats) => [{ id, title: 'New chat' }, ...chats]);
    this.selectedId.set(id);
  }

  protected toggle(): void {
    this.animating.set(true);
    this.open.update((open) => !open);
    clearTimeout(this.animationTimer);
    this.animationTimer = setTimeout(() => this.animating.set(false), this.animationMs());
  }

  protected rename(id: number, title: string): void {
    this.chats.update((chats) => chats.map((chat) => (chat.id === id ? { ...chat, title } : chat)));
  }

  protected remove(id: number): void {
    this.chats.update((chats) => chats.filter((chat) => chat.id !== id));
    if (this.selectedId() === id) {
      this.selectedId.set(null);
    }
  }

  private animationMs(): number {
    const raw = getComputedStyle(this.host.nativeElement).getPropertyValue('--sidenav-duration').trim();
    const value = Number.parseFloat(raw);
    if (!Number.isFinite(value)) {
      return 0;
    }
    return raw.endsWith('ms') ? value : value * 1000;
  }
}
