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

  protected readonly editing = signal(false);
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
  }

  protected choose(): void {
    this.selectedChange.emit();
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
