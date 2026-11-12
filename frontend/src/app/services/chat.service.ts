import { filter } from "rxjs";
import { Chat } from "../contracts/chat";
import { Message } from "../contracts/message";
import { Injectable, signal } from "@angular/core";

@Injectable({ providedIn: "root" })
export class ChatService {

    public messages = signal<Message[]>([])
    
    private chats: Chat[] = [];
    private nextChatId: number = 0;
    private currentChatId: number = 0;

    loadChat = (id: number) => {
        if (id < 0)
            throw new Error("Chat id must be greater than 0");
        const filteredChats = this.chats.filter(chat => chat.id == id);
        if (filteredChats.length == 0)
            throw new Error("Chat with id " + this.currentChatId + " does not exist");
        filteredChats[0].messages ??= [];
        this.messages.set(filteredChats[0].messages);
    }

    addChat = (name: string): number => {
        this.chats.push({
            id: this.nextChatId,
            name: name
        });
        return this.nextChatId++;
    }

    addMessage = (messageText: string, isPrompt: boolean) => {
        const filteredChats = this.chats.filter(chat => chat.id == this.currentChatId);
        filteredChats[0].messages ??= [];
        filteredChats[0].messages.push({
            message: messageText,
            isPrompt: isPrompt,
            timestamp: Date.now()
        });
    }

    // getCurrentChat = (): Chat => {
    //     return this.chats[this.currentChatId];
    // }

    // getChatById = (id: number): Chat => {
    //     const filteredChats = this.chats.filter(chat => chat.id == id);
    //     if (id < 0)
    //         throw new Error("Chat id must be greater than 0");
    //     if (filteredChats.length == 0)
    //         throw new Error("Could not find chat with id " + id);
    //     return filteredChats[0];
    // }

    getAllChats = (): Chat[] => {
        return this.chats;
    }

    renameChat = (chatId: number, name: string) => {
        const filteredChats = this.chats.filter(chat => chat.id != chatId);
        if (chatId < 0)
            throw new Error("Chat id must be greater than 0");
        if (this.chats == filteredChats)
            throw new Error("Could not find chat with id " + chatId);
        filteredChats[0].name = name;
    } 

    removeChatById = (id: number) => {
        const filteredChats = this.chats.filter(chat => chat.id != id);
        if (id < 0)
            throw new Error("Chat id must be greater than 0");
        if (this.chats == filteredChats)
            throw new Error("Could not find chat with id " + id);
        this.chats = filteredChats;
    } 

}