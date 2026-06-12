import { Component, ElementRef, effect, inject, signal, viewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { TextFieldModule } from '@angular/cdk/text-field';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { marked } from 'marked';

import { ChatService } from '../../core/api/chat.service';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-chat',
  imports: [
    FormsModule,
    TextFieldModule,
    MatButtonModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
  ],
  templateUrl: './chat.html',
})
export class Chat {
  private readonly chat = inject(ChatService);

  private readonly scrollContainer = viewChild<ElementRef<HTMLDivElement>>('scrollContainer');

  readonly messages = signal<ChatMessage[]>([]);
  readonly draft = signal('');
  readonly streaming = signal(false);
  readonly error = signal<string | null>(null);

  private threadId: string | null = null;

  constructor() {
    // Keep the conversation scrolled to the newest message as it streams in.
    effect(() => {
      this.messages();
      this.streaming();
      const el = this.scrollContainer()?.nativeElement;
      if (el) {
        requestAnimationFrame(() => (el.scrollTop = el.scrollHeight));
      }
    });
  }

  /**
   * Render assistant markdown to HTML. Bound via [innerHTML], which Angular's
   * DomSanitizer cleans automatically — important since this is LLM output.
   * marked handles partial/incomplete markdown gracefully during streaming.
   */
  renderMarkdown(content: string): string {
    return marked.parse(content, { async: false, gfm: true, breaks: true });
  }

  onEnter(event: Event): void {
    const keyEvent = event as KeyboardEvent;
    // Shift+Enter inserts a newline; Enter alone sends.
    if (keyEvent.shiftKey) return;
    keyEvent.preventDefault();
    this.send();
  }

  async send(): Promise<void> {
    const text = this.draft().trim();
    if (!text || this.streaming()) return;

    this.error.set(null);
    this.messages.update((m) => [
      ...m,
      { role: 'user', content: text },
      { role: 'assistant', content: '' },
    ]);
    this.draft.set('');
    this.streaming.set(true);

    try {
      const stream = this.chat.stream(text, this.threadId, (id) => (this.threadId = id));
      for await (const chunk of stream) {
        this.appendToLast(chunk);
      }
    } catch {
      this.error.set('Something went wrong reaching the assistant. Please try again.');
      this.dropEmptyAssistant();
    } finally {
      this.streaming.set(false);
    }
  }

  reset(): void {
    if (this.streaming()) return;
    this.messages.set([]);
    this.threadId = null;
    this.error.set(null);
  }

  private appendToLast(text: string): void {
    this.messages.update((msgs) => {
      const copy = [...msgs];
      const last = copy[copy.length - 1];
      copy[copy.length - 1] = { ...last, content: last.content + text };
      return copy;
    });
  }

  private dropEmptyAssistant(): void {
    this.messages.update((msgs) => {
      const last = msgs[msgs.length - 1];
      return last?.role === 'assistant' && last.content === '' ? msgs.slice(0, -1) : msgs;
    });
  }
}