import { Component, computed, inject, input} from '@angular/core';
import { DomSanitizer } from '@angular/platform-browser';
import { Message } from '../../contracts/message';
import { DatePipe } from '@angular/common';
import { Badges } from '../badges/badges';
import { CopyBadge } from '../copy-badge/copy-badge';
import { renderMarkdown } from './markdown';

@Component({
  selector: 'app-chat-bubble',
  imports: [DatePipe, Badges, CopyBadge],
  templateUrl: './chat-bubble.html',
  styleUrl: './chat-bubble.css',
})
export class ChatBubble {
  private readonly sanitizer = inject(DomSanitizer);

  message = input<Message>({
    message: "Message could not be loaded.",
    isPrompt: false,
    timestamp: 0
  });

  // markdown-it is the only source of these tags, and it escapes raw HTML.
  protected readonly html = computed(() =>
    this.sanitizer.bypassSecurityTrustHtml(renderMarkdown(this.message().message)),
  );
}
