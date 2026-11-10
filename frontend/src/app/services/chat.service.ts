import { filter } from "rxjs";
import { Chat } from "../contracts/chat";
import { Message } from "../contracts/message";


export class ChatService {

    chats: Chat[] = [];
    currentId: number = 0;

    addChat = (name: string) => {
        this.chats.push({
            id: this.currentId++,
            name: name
        });
    }

    findChatById = (id: number) => {
        const filteredChats = this.chats.filter(chat => chat.id == id);
        if (filteredChats.length == 0)
            throw new Error("Could not find chat with id " + id);
        return filteredChats[0];
    }

    removeChatById = (id: number) => {
        const filteredChats = this.chats.filter(chat => chat.id != id);
        if (this.chats == filteredChats)
            throw new Error("Could not find chat with id " + id);
        this.chats = filteredChats;
    } 

}