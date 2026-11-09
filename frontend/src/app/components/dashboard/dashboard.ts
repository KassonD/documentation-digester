import { Component } from '@angular/core';
import { WelcomeMessage } from '../welcome-message/welcome-message';
import { ChatBar } from '../chat-bar/chat-bar';

@Component({
  selector: 'app-dashboard',
  imports: [WelcomeMessage, ChatBar],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
})
export class Dashboard {
  
}
