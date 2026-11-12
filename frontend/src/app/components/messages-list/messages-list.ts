import { Component, inject, input, signal } from '@angular/core';
import { Message } from '../../contracts/message';
import { ChatBubble } from '../chat-bubble/chat-bubble';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-messages-list',
  imports: [ChatBubble],
  templateUrl: './messages-list.html',
  styleUrl: './messages-list.css',
})
export class MessagesList {
  chatService = inject(ChatService);
}
