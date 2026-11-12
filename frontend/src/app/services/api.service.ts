import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

export interface ChatSource {
  title: string;
  source_path: string;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
}

export interface ChatSourcesEvent {
  type: 'sources';
  session_id: string;
  sources: ChatSource[];
}

export interface ChatTokenEvent {
  type: 'token';
  text: string;
}

export interface ChatDoneEvent {
  type: 'done';
}

export interface ChatErrorEvent {
  type: 'error';
  message: string;
}

export type ChatStreamEvent = ChatSourcesEvent | ChatTokenEvent | ChatDoneEvent | ChatErrorEvent;

@Injectable({ providedIn: 'root' })
export class ApiService {
  private readonly streamUrl = '/chat/stream';

  ask(question: string, sessionId?: string | null): Observable<ChatStreamEvent> {
    const body: ChatRequest = { question };
    if (sessionId) {
      body.session_id = sessionId;
    }

    return new Observable((subscriber) => {
      const controller = new AbortController();

      fetch(this.streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/x-ndjson',
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })
        .then(async (response) => {
          if (!response.ok || !response.body) {
            throw new Error(`Chat stream failed (${response.status})`);
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let buffer = '';

          // One JSON object per line. A read can split a line, so the unfinished tail stays in the buffer.
          while (true) {
            const { done, value } = await reader.read();
            if (done) {
              break;
            }
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() ?? '';
            for (const line of lines) {
              this.emit(subscriber, line);
            }
          }

          buffer += decoder.decode();
          this.emit(subscriber, buffer);
          subscriber.complete();
        })
        .catch((error: unknown) => {
          // Unsubscribe aborts the fetch. That cancel is not a failed answer.
          if (error instanceof DOMException && error.name === 'AbortError') {
            subscriber.complete();
            return;
          }
          subscriber.error(error);
        });

      return () => controller.abort();
    });
  }

  private emit(subscriber: { next: (event: ChatStreamEvent) => void }, line: string): void {
    const trimmed = line.trim();
    if (!trimmed) {
      return;
    }
    subscriber.next(JSON.parse(trimmed) as ChatStreamEvent);
  }
}
