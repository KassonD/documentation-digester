import { Component } from '@angular/core';
import { WelcomeMessage } from '../welcome-message/welcome-message';
import { ChatBar } from '../chat-bar/chat-bar';
import { MessagesList } from '../messages-list/messages-list';

@Component({
  selector: 'app-dashboard',
  imports: [WelcomeMessage, ChatBar, MessagesList],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {

  chatStarted = false;
  currentChatName: string = 'New Chat';

  onQuestionSubmitted(question: string) {
    this.chatStarted = true;
  }
  
}
