import { ChatResponse, HealthStatus } from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');

export async function checkHealth(): Promise<HealthStatus> {
  const res = await fetch(`${API_BASE_URL}/health`);
  if (!res.ok) {
    throw new Error(`Health check failed: ${res.statusText}`);
  }
  return res.json();
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
  systemPrompt?: string,
  simulateFailureHeader?: string
): Promise<ChatResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (simulateFailureHeader) {
    headers['X-Simulate-Failure'] = simulateFailureHeader;
  }

  const payload: { session_id: string; message: string; system_prompt?: string } = {
    session_id: sessionId,
    message: message.trim(),
  };

  if (systemPrompt && systemPrompt.trim()) {
    payload.system_prompt = systemPrompt.trim();
  }

  const res = await fetch(`${API_BASE_URL}/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    let errorDetail = `Request failed with status ${res.status}`;
    try {
      const errJson = await res.json();
      if (errJson && errJson.detail) {
        if (typeof errJson.detail === 'string') {
          errorDetail = errJson.detail;
        } else if (Array.isArray(errJson.detail)) {
          errorDetail = errJson.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
        }
      }
    } catch {
      // ignore json parse error
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export async function fetchSessionHistory(sessionId: string) {
  const res = await fetch(`${API_BASE_URL}/sessions/${sessionId}/messages`);
  if (!res.ok) {
    if (res.status === 404) {
      return { session_id: sessionId, messages: [] };
    }
    throw new Error(`Failed to fetch history: ${res.statusText}`);
  }
  return res.json();
}
