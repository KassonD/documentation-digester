import { DatePipe } from '@angular/common';
import { Component } from '@angular/core';
import { Message } from '../../contracts/message';
import { ChatBubble } from '../chat-bubble/chat-bubble';

@Component({
  selector: 'app-messages-list',
  imports: [ChatBubble, DatePipe],
  templateUrl: './messages-list.html',
  styleUrl: './messages-list.css',
})
export class MessagesList {

  messageList: Message[] = [
    {
      message: "Hello",
      isPrompt: true,
      timestamp: Date.now() - 180_000,
    },
    {
      message: "Hi!",
      isPrompt: false,
      timestamp: Date.now() - 150_000,
      source: "classes/class_node.rst",
    },
    {
      message: "What is your name",
      isPrompt: true,
      timestamp: Date.now() - 90_000,
    },
    {
      message: "My name is Godot Docbot!",
      isPrompt: false,
      timestamp: Date.now() - 60_000,
      source: "getting_started/introduction.rst",
    },
    {
      message: "My name is Godot Docbot!",
      isPrompt: false,
      timestamp: Date.now() - 60_000,
      source: "getting_started/introduction.rst",
    },
  ];

  sourceParts(source: string): string[] {
    return source.split('/').filter((part) => part.length > 0);
  }

}
