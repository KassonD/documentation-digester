
export interface Message {
    message: string,
    isPrompt: boolean,
    timestamp: number,
    source?: string[],
}