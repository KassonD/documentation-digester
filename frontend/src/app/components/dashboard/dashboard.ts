import { Component, inject } from '@angular/core';
import { ChatService } from '../../services/chat.service';
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
  private readonly chats = inject(ChatService);

  get chatStarted(): boolean {
    return this.chats.messages().length > 0;
  }

  get currentChatName(): string {
    const id = this.chats.selectedId();
    return this.chats.chatList().find((chat) => chat.id === id)?.name ?? 'New Chat';
  }

  onQuestionSubmitted(question: string) {
    this.chats.ask(question);
  }
}
