import { Component, EventEmitter, Output } from '@angular/core';

@Component({
  imports: [],
  selector: 'app-welcome-message',
  styleUrl: './welcome-message.css',
  templateUrl: './welcome-message.html',
})
export class WelcomeMessage {
  @Output() questionSelected = new EventEmitter<string>();

  readonly starters = [
    'How do signals work?',
    'How do I write a shader?',
    'What is a scene?',
  ];

  choose(question: string): void {
    this.questionSelected.emit(question);
  }
}
