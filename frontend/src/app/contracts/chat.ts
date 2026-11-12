import { Message } from "./message";

export interface Chat {
    id: number,
    name: string,
    messages?: Message[],
    // Server conversation id. The next question sends it back so the follow-up stays in this chat.
    sessionId?: string,
}
