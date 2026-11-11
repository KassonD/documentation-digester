import { Component, EventEmitter, Output, ViewChild, ElementRef } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  imports: [FormsModule],
  selector: 'app-chat-bar',
  styleUrl: './chat-bar.css',
  templateUrl: './chat-bar.html',
})

export class ChatBar {
  @Output() questionSubmitted = new EventEmitter<string>();

  @ViewChild('chatInput') chatInput!: ElementRef<HTMLTextAreaElement>;

  question = '';

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
    if (this.question.trim()) {
      this.questionSubmitted.emit(this.question);
      this.question = '';

      const textarea = this.chatInput.nativeElement;
      textarea.style.height = 'auto';
    }
  }
}
