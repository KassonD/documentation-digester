import { afterRenderEffect, Component, ElementRef, inject, viewChild } from '@angular/core';
import { ChatService } from '../../services/chat.service';
import { ChatBubble } from '../chat-bubble/chat-bubble';
import { ResponseLoader } from '../response-loader/response-loader';

@Component({
  selector: 'app-messages-list',
  imports: [ChatBubble, ResponseLoader],
  templateUrl: './messages-list.html',
  styleUrl: './messages-list.css',
})
export class MessagesList {
  chatService = inject(ChatService);
  private readonly thread = viewChild<ElementRef<HTMLElement>>('thread');

  constructor() {
    // Reading the latest text and the loader flag is what makes this run again as tokens arrive.
    afterRenderEffect(() => {
      const messages = this.chatService.messages();
      const last = messages[messages.length - 1];
      void last?.message;
      void this.awaitingReply;
      this.scrollToBottom();
    });
  }

  get awaitingReply(): boolean {
    const id = this.chatService.selectedId();
    if (id === null || !this.chatService.pendingIds().has(id))
      return false;
    const messages = this.chatService.messages();
    const last = messages[messages.length - 1];
    // Dots only until reply text exists. The search bar stays locked through pendingIds until the stream ends.
    return !last || last.isPrompt;
  }

  private scrollToBottom(): void {
    const thread = this.thread()?.nativeElement;
    if (!thread) {
      return;
    }
    thread.scrollTop = thread.scrollHeight;
  }
}
