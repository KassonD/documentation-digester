import { Subscription } from "rxjs";
import { Chat } from "../contracts/chat";
import { Message } from "../contracts/message";
import { Injectable, inject, signal } from "@angular/core";
import { ApiService } from "./api.service";

@Injectable({ providedIn: "root" })
export class ChatService {
    private readonly api = inject(ApiService);
    private readonly replyFailed = "The docbot could not answer that. Try again.";

    public messages = signal<Message[]>([])
    readonly chatList = signal<Chat[]>([]);
    readonly selectedId = signal<number | null>(null);
    // Chats whose stream is still open. The search bar reads this and stays locked until the stream ends.
    readonly pendingIds = signal<ReadonlySet<number>>(new Set());

    private nextChatId: number = 0;
    // One live stream per chat. The generation lets a newer ask() ignore events from the stream it replaced.
    private readonly streams = new Map<number, Subscription>();
    private readonly requestGen = new Map<number, number>();

    loadChat = (id: number) => {
        if (id < 0)
            throw new Error("Chat id cannot be negative");
        const chat = this.findChat(id);
        if (!chat)
            throw new Error("Chat with id " + id + " does not exist");
        chat.messages ??= [];
        this.selectedId.set(id);
        this.messages.set([...chat.messages]);
    }

    addChat = (name: string): number => {
        const id = this.nextChatId++;
        this.chatList.update(chats => [...chats, {
            id: id,
            name: name
        }]);
        return id;
    }

    addMessage = (messageText: string, isPrompt: boolean) => {
        const chat = this.findChat(this.selectedId());
        if (!chat)
            throw new Error("No chat is selected");
        chat.messages ??= [];
        chat.messages.push({
            message: messageText,
            isPrompt: isPrompt,
            timestamp: Date.now()
        });
        this.messages.set([...chat.messages]);
    }

    renameChat = (chatId: number, name: string) => {
        if (chatId < 0)
            throw new Error("Chat id cannot be negative");
        const chat = this.findChat(chatId);
        if (!chat)
            throw new Error("Could not find chat with id " + chatId);
        chat.name = name;
        // The name is changed on the object. A new array is what tells the sidebar to draw it.
        this.chatList.set([...this.chatList()]);
    }

    removeChatById = (id: number) => {
        if (id < 0)
            throw new Error("Chat id cannot be negative");
        const chats = this.chatList();
        const filteredChats = chats.filter(chat => chat.id != id);
        if (filteredChats.length == chats.length)
            throw new Error("Could not find chat with id " + id);
        this.cancelStream(id);
        this.setPending(id, false);
        this.chatList.set(filteredChats);
        if (this.selectedId() == id) {
            this.selectedId.set(null);
            this.messages.set([]);
        }
    }

    ask(question: string): void {
        const text = question.trim();
        if (!text)
            return;

        let chatId = this.selectedId();
        if (chatId === null) {
            chatId = this.addChat(this.titleFrom(text));
            this.loadChat(chatId);
        } else {
            const chat = this.findChat(chatId);
            if (chat && chat.name === "New chat" && (chat.messages?.length ?? 0) === 0)
                this.renameChat(chat.id, this.titleFrom(text));
        }
        const generation = this.beginRequest(chatId);
        this.addMessage(text, true);

        // The server sends sources before any reply text. Hold them until the first visible chunk opens the bubble.
        let pendingSources: string[] | undefined;
        this.setPending(chatId, true);
        const sessionId = this.findChat(chatId)?.sessionId;

        const subscription = this.api.ask(text, sessionId).subscribe({
            next: (event) => {
                if (!this.isCurrentRequest(chatId, generation))
                    return;
                if (event.type === "sources") {
                    const chat = this.findChat(chatId);
                    if (chat)
                        chat.sessionId = event.session_id;
                    pendingSources = [...new Set(event.sources.map((source) => source.source_path))];
                    return;
                }
                if (event.type === "token") {
                    if (this.show(chatId, event.text, pendingSources))
                        pendingSources = undefined;
                    return;
                }
                if (event.type === "error")
                    this.fail(chatId, event.message || this.replyFailed);
            },
            error: () => {
                if (!this.isCurrentRequest(chatId, generation))
                    return;
                this.streams.delete(chatId);
                this.fail(chatId, this.replyFailed);
            },
            complete: () => {
                if (!this.isCurrentRequest(chatId, generation))
                    return;
                this.streams.delete(chatId);
                const chat = this.findChat(chatId);
                const last = chat?.messages?.[chat.messages.length - 1];
                if (!last || last.isPrompt)
                    this.show(chatId, this.replyFailed, pendingSources);
                this.setPending(chatId, false);
            },
        });
        this.streams.set(chatId, subscription);
    }

    private beginRequest(id: number): number {
        const generation = (this.requestGen.get(id) ?? 0) + 1;
        // Bump first. Unsubscribing completes the old stream, and that completion must see the new generation.
        this.requestGen.set(id, generation);
        this.streams.get(id)?.unsubscribe();
        this.streams.delete(id);
        return generation;
    }

    private cancelStream(id: number): void {
        this.requestGen.delete(id);
        this.streams.get(id)?.unsubscribe();
        this.streams.delete(id);
    }

    private isCurrentRequest(id: number, generation: number): boolean {
        return this.requestGen.get(id) === generation;
    }

    private findChat(id: number | null): Chat | undefined {
        return this.chatList().find(item => item.id == id);
    }

    private titleFrom(question: string): string {
        const line = question.split("\n")[0].trim();
        return line.length > 42 ? line.slice(0, 42).trimEnd() + "…" : line;
    }

    private fail(id: number, message: string): void {
        // A failure after tokens must stay its own bubble. Appending would glue the error onto the partial answer.
        this.show(id, message, undefined, true);
        this.setPending(id, false);
    }

    private show(id: number, text: string, sources?: string[], startNew = false): boolean {
        const chat = this.findChat(id);
        if (!chat)
            return false;
        chat.messages ??= [];
        const last = chat.messages[chat.messages.length - 1];
        if (!startNew && last && !last.isPrompt) {
            chat.messages[chat.messages.length - 1] = { ...last, message: last.message + text };
        } else if (text.trim()) {
            chat.messages.push({ message: text, isPrompt: false, timestamp: Date.now(), sources });
        } else {
            // A blank chunk is not a reply yet, so the caller keeps the sources for the next chunk.
            return false;
        }
        if (this.selectedId() == id)
            this.messages.set([...chat.messages]);
        return true;
    }

    private setPending(id: number, pending: boolean): void {
        this.pendingIds.update((ids) => {
            if (ids.has(id) === pending)
                return ids;
            const next = new Set(ids);
            if (pending)
                next.add(id);
            else
                next.delete(id);
            return next;
        });
    }
}
