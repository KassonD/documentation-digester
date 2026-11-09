import { Component, EventEmitter, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';

@Component({
  imports: [FormsModule],
  selector: 'app-chat-bar',
  styleUrl: './chat-bar.css',
  templateUrl: './chat-bar.html',
})
export class ChatBar {
  @Output() questionSubmitted = new EventEmitter<string>();

  question = '';

  sendQuestion() {
    if (this.question.trim()) {
      this.questionSubmitted.emit(this.question);
      this.question = '';
    }
  }
}
