export interface ChatMetadata {
  resolution_source: 'LIVE_INFERENCE' | 'LLM_CACHE';
  model: string;
  latency_ms: number;
  input_tokens: number;
  output_tokens: number;
  key_id?: string | null;
  fallback_attempts: number;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
  metadata: ChatMetadata;
}

export interface MessageItem {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  metadata?: ChatMetadata;
  timestamp: string;
  isError?: boolean;
}

export interface HealthStatus {
  status: string;
  keys_configured: number;
  cache_enabled: boolean;
}
