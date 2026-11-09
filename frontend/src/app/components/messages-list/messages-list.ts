import { Component } from '@angular/core';
import { Message } from '../../contracts/message';
import { ChatBubble } from '../chat-bubble/chat-bubble';

@Component({
  selector: 'app-messages-list',
  imports: [ChatBubble],
  templateUrl: './messages-list.html',
  styleUrl: './messages-list.css',
})
export class MessagesList {

  messageList: Message[] = [
    {
      message: "Hello",
      isPrompt: true,
      timestamp: Date.now()
    },
    {
      message: "Hi!",
      isPrompt: false,
      timestamp: Date.now()
    },
    {
      message: "What is your name",
      isPrompt: true,
      timestamp: Date.now()
    },
    {
      message: "My name is Godot Docbot!",
      isPrompt: false,
      timestamp: Date.now()
    },
  ]

}
