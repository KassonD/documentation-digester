import { Component, ElementRef, effect, inject, signal, viewChild } from '@angular/core';
import { ChatService } from '../../services/chat.service';
import { ChatHistoryItem } from '../chat-history-item/chat-history-item';

const themeKey = 'theme';

function readNebula(): boolean {
  try {
    return localStorage.getItem(themeKey) === 'nebula';
  } catch {
    return false;
  }
}

function storeTheme(nebula: boolean): void {
  try {
    if (nebula) {
      localStorage.setItem(themeKey, 'nebula');
    } else {
      localStorage.removeItem(themeKey);
    }
  } catch {
    // Storage can be blocked. The in-page toggle still works.
  }
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
  private readonly chatsService = inject(ChatService);
  private readonly settingsRoot = viewChild<ElementRef<HTMLElement>>('settingsRoot');
  private animationTimer?: ReturnType<typeof setTimeout>;

  protected readonly chats = this.chatsService.chatList;
  protected readonly selectedId = this.chatsService.selectedId;
  protected readonly open = signal(true);
  protected readonly animating = signal(false);
  protected readonly settingsMenu = signal(false);
  protected readonly theme = signal(readNebula());

  constructor() {
    effect(() => {
      const nebula = this.theme();
      if (nebula) {
        document.documentElement.dataset['theme'] = 'nebula';
      } else {
        delete document.documentElement.dataset['theme'];
      }
      storeTheme(nebula);
    });

    effect((onCleanup) => {
      if (!this.settingsMenu()) {
        return;
      }

      const close = (event: PointerEvent) => {
        const root = this.settingsRoot()?.nativeElement;
        if (!root?.contains(event.target as Node)) {
          this.settingsMenu.set(false);
        }
      };
      const onKey = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          this.settingsMenu.set(false);
        }
      };

      document.addEventListener('pointerdown', close);
      document.addEventListener('keydown', onKey);
      onCleanup(() => {
        document.removeEventListener('pointerdown', close);
        document.removeEventListener('keydown', onKey);
      });
    });
  }

  protected select(id: number): void {
    this.chatsService.loadChat(id);
  }

  protected create(): void {
    const id = this.chatsService.addChat('New chat');
    this.chatsService.loadChat(id);
  }

  protected toggle(): void {
    this.animating.set(true);
    this.open.update((open) => !open);
    if (!this.open()) {
      this.settingsMenu.set(false);
    }
    clearTimeout(this.animationTimer);
    this.animationTimer = setTimeout(() => this.animating.set(false), this.animationMs());
  }

  protected toggleSettings(): void {
    this.settingsMenu.update((open) => !open);
  }

  protected toggleTheme(): void {
    this.theme.update((on) => !on);
  }

  protected rename(id: number, title: string): void {
    this.chatsService.renameChat(id, title);
  }

  protected remove(id: number): void {
    this.chatsService.removeChatById(id);
  }

  // The stylesheet stores seconds ("0.35s") or milliseconds. The timer needs milliseconds.
  private animationMs(): number {
    const raw = getComputedStyle(this.host.nativeElement).getPropertyValue('--sidenav-duration').trim();
    const value = Number.parseFloat(raw);
    if (!Number.isFinite(value)) {
      return 0;
    }
    return raw.endsWith('ms') ? value : value * 1000;
  }
}
