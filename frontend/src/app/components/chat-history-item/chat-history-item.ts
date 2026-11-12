import { Component, ElementRef, effect, inject, input, output, signal } from '@angular/core';

@Component({
  selector: 'app-chat-history-item',
  templateUrl: './chat-history-item.html',
  styleUrl: './chat-history-item.css',
})
export class ChatHistoryItem {
  private readonly host = inject(ElementRef<HTMLElement>);

  readonly title = input.required<string>();
  readonly selected = input(false);
  readonly titleChange = output<string>();
  readonly selectedChange = output<void>();
  readonly deleted = output<void>();

  protected readonly editing = signal(false);
  protected readonly menu = signal(false);
  protected readonly menuAbove = signal(false);
  protected readonly draft = signal('');
  private ignoreBlur = false;

  constructor() {
    effect((onCleanup) => {
      if (!this.editing()) {
        return;
      }

      const stop = (event: PointerEvent) => {
        if (!this.host.nativeElement.contains(event.target as Node)) {
          this.save();
        }
      };

      document.addEventListener('pointerdown', stop);
      onCleanup(() => document.removeEventListener('pointerdown', stop));
    });

    effect((onCleanup) => {
      if (!this.menu()) {
        return;
      }

      const close = (event: PointerEvent) => {
        if (!this.host.nativeElement.contains(event.target as Node)) {
          this.menu.set(false);
        }
      };
      const onKey = (event: KeyboardEvent) => {
        if (event.key === 'Escape') {
          this.menu.set(false);
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

  protected choose(): void {
    this.selectedChange.emit();
  }

  protected toggleMenu(event: Event): void {
    this.choose();
    if (this.menu()) {
      this.menu.set(false);
      return;
    }

    const button = event.currentTarget as HTMLElement;
    const list = this.host.nativeElement.closest('ul');
    const buttonRect = button.getBoundingClientRect();
    const listBottom = list?.getBoundingClientRect().bottom ?? window.innerHeight;
    this.menuAbove.set(listBottom - buttonRect.bottom < 72);
    this.menu.set(true);
  }

  protected rename(): void {
    this.menu.set(false);
    this.edit();
  }

  protected remove(): void {
    this.menu.set(false);
    this.deleted.emit();
  }

  protected edit(): void {
    this.choose();
    this.draft.set(this.title());
    this.editing.set(true);
    setTimeout(() => {
      const input = this.host.nativeElement.querySelector('input');
      if (input) {
        this.fit(input);
        input.focus();
        input.select();
      }
    });
  }

  protected onDraft(event: Event): void {
    const input = event.target as HTMLInputElement;
    this.draft.set(input.value);
    this.fit(input);
  }

  private fit(input: HTMLInputElement): void {
    const max = input.parentElement?.clientWidth ?? Number.POSITIVE_INFINITY;
    input.style.width = '0px';
    const chrome = input.offsetWidth;
    const content = input.scrollWidth + 2;
    const capped = Math.min(content, Math.max(0, max - chrome));
    input.style.width = `${capped}px`;
    input.scrollLeft = content > capped ? input.scrollWidth : 0;
  }

  protected save(): void {
    if (this.ignoreBlur) {
      this.ignoreBlur = false;
      return;
    }

    const next = this.draft().trim();
    if (next && next !== this.title()) {
      this.titleChange.emit(next);
    }
    this.editing.set(false);
  }

  protected cancel(): void {
    this.ignoreBlur = true;
    this.editing.set(false);
  }
}
