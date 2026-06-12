import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { ChatResponse } from '../models';
import { AuthService } from '../auth/auth.service';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly base = `${environment.apiUrl}/chat`;

  /** Non-streaming request — returns the full response and the thread id. */
  send(message: string, threadId?: string | null): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(this.base, {
      message,
      thread_id: threadId ?? null,
    });
  }

  /**
   * Streaming request via SSE. Yields text chunks as they arrive.
   * The server returns the conversation's thread id in the `X-Thread-ID` header,
   * surfaced through the `onThreadId` callback.
   */
  async *stream(
    message: string,
    threadId: string | null,
    onThreadId?: (id: string) => void,
    signal?: AbortSignal,
  ): AsyncGenerator<string> {
    const res = await fetch(`${this.base}/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.auth.token() ?? ''}`,
      },
      body: JSON.stringify({ message, thread_id: threadId }),
      signal,
    });

    const id = res.headers.get('X-Thread-ID');
    if (id && onThreadId) onThreadId(id);

    if (!res.body) return;

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const frames = buffer.split('\n\n');
      buffer = frames.pop() ?? '';

      for (const frame of frames) {
        const idx = frame.indexOf('data:');
        if (idx === -1) continue;
        const payload = frame.slice(idx + 5).trim();
        if (payload === '[DONE]') return;
        yield JSON.parse(payload) as string;
      }
    }
  }
}
