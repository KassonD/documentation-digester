import { Component, input} from '@angular/core';

@Component({
  selector: 'app-chat-bubble',
  imports: [],
  templateUrl: './chat-bubble.html',
  styleUrl: './chat-bubble.css',
})
export class ChatBubble {
  message = input<string>("");
  isPrompt = input<boolean>(true);

  constructor() {
    console.log(this.isPrompt());
  }

}
