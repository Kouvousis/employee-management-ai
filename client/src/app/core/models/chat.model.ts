export interface ChatRequest {
  message: string;
  thread_id?: string | null;
}

export interface ChatResponse {
  response: string;
  thread_id: string;
}