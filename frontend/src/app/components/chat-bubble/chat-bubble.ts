import { Component, input} from '@angular/core';
import { Message } from '../../contracts/message';
import { DatePipe } from '@angular/common';

@Component({
  selector: 'app-chat-bubble',
  imports: [DatePipe],
  templateUrl: './chat-bubble.html',
  styleUrl: './chat-bubble.css',
})
export class ChatBubble {
  message = input<Message>({
    message: "Message could not be loaded.",
    isPrompt: false,
    timestamp: 0
  });

  constructor() {
    console.log(this.message().isPrompt);
  }

  sourceParts(source: string): string[] {
    return source.split('/').filter((part) => part.length > 0);
  }
}
