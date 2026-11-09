import { Component } from '@angular/core';
import { WelcomeMessage } from '../welcome-message/welcome-message';
import { ChatBar } from '../chat-bar/chat-bar';
import { ChatBubble } from '../chat-bubble/chat-bubble';
import { MessagesList } from '../messages-list/messages-list';

@Component({
  selector: 'app-dashboard',
  imports: [WelcomeMessage, ChatBar, ChatBubble, MessagesList],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {

  chatStarted = false;

  onQuestionSubmitted(question: string) {
    this.chatStarted = true;
  }
  
}
