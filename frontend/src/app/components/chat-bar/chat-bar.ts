import { Component, EventEmitter, Output, ViewChild, ElementRef, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ChatService } from '../../services/chat.service';

@Component({
  imports: [FormsModule],
  selector: 'app-chat-bar',
  styleUrl: './chat-bar.css',
  templateUrl: './chat-bar.html',
})

export class ChatBar {
  private readonly chats = inject(ChatService);

  @Output() questionSubmitted = new EventEmitter<string>();

  @ViewChild('chatInput') chatInput!: ElementRef<HTMLTextAreaElement>;

  question = '';

  // Locked for the whole stream, including while tokens are still arriving.
  get locked(): boolean {
    const id = this.chats.selectedId();
    return id !== null && this.chats.pendingIds().has(id);
  }

  resizeTextarea() {
    const textarea = this.chatInput.nativeElement;

    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
  }

  handleEnter(event: Event) {
    const keyboardEvent = event as KeyboardEvent;

    if (!keyboardEvent.shiftKey) {
      keyboardEvent.preventDefault();
      this.sendQuestion();
    }
  }

  sendQuestion() {
    if (this.locked)
      return;
    if (this.question.trim()) {
      this.questionSubmitted.emit(this.question);
      this.question = '';

      const textarea = this.chatInput.nativeElement;
      textarea.style.height = 'auto';
    }
  }
}
