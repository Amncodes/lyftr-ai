import React, { useState, useEffect, useRef } from 'react';
import { Menu, Loader2 } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { ChatMessage } from './components/ChatMessage';
import { ChatInput } from './components/ChatInput';
import { WelcomeScreen } from './components/WelcomeScreen';
import { MessageItem, HealthStatus } from './types';
import { sendChatMessage, checkHealth, fetchSessionHistory } from './services/api';

function generateSessionId(): string {
  const randomPart = Math.random().toString(36).substring(2, 8);
  return `s-${randomPart}`;
}

export const App: React.FC = () => {
  const [sessionId, setSessionId] = useState<string>(() => generateSessionId());
  const [messages, setMessages] = useState<MessageItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [systemPrompt, setSystemPrompt] = useState('');
  const [simFailure, setSimFailure] = useState('');
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [mobileOpen, setMobileOpen] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom of messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Fetch health on load and periodically
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const data = await checkHealth();
        setHealth(data);
      } catch {
        setHealth({ status: 'unhealthy', keys_configured: 0, cache_enabled: false });
      }
    };
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // When session ID changes, load its history if any
  useEffect(() => {
    let active = true;
    const loadHistory = async () => {
      try {
        const res = await fetchSessionHistory(sessionId);
        if (active && res && res.messages && res.messages.length > 0) {
          const formatted: MessageItem[] = res.messages.map((m: any, idx: number) => ({
            id: `${sessionId}-${idx}`,
            role: m.role,
            content: m.content,
            metadata: m.metadata,
            timestamp: new Date().toISOString(),
          }));
          setMessages(formatted);
        } else if (active) {
          setMessages([]);
        }
      } catch {
        if (active) setMessages([]);
      }
    };
    loadHistory();
    return () => {
      active = false;
    };
  }, [sessionId]);

  const handleNewChat = () => {
    const newId = generateSessionId();
    setSessionId(newId);
    setMessages([]);
  };

  const handleSendMessage = async (text: string, prompt?: string) => {
    if (!text.trim() || loading) return;

    const userMessage: MessageItem = {
      id: `usr-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await sendChatMessage(
        sessionId,
        text,
        prompt || undefined,
        simFailure || undefined
      );

      const assistantMessage: MessageItem = {
        id: `asst-${Date.now()}`,
        role: 'assistant',
        content: response.reply,
        metadata: response.metadata,
        timestamp: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err: any) {
      // Readable error message bubble
      const errorMessage: MessageItem = {
        id: `err-${Date.now()}`,
        role: 'assistant',
        content: `⚠️ Error: ${err.message || 'Service unavailable. Please retry.'}`,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0a0e17] text-slate-100 font-sans">
      {/* Sidebar */}
      <Sidebar
        sessionId={sessionId}
        onNewChat={handleNewChat}
        health={health}
        simFailure={simFailure}
        onSimFailureChange={setSimFailure}
        mobileOpen={mobileOpen}
        onCloseMobile={() => setMobileOpen(false)}
      />

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col h-full overflow-hidden relative">
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between p-3.5 border-b border-slate-800 bg-[#0d121f]">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800"
          >
            <Menu size={20} />
          </button>
          <span className="font-semibold text-sm">Lyftr AI</span>
          <div className="w-8" />
        </header>

        {/* Messages or Welcome View */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          {messages.length === 0 ? (
            <WelcomeScreen onSelectPrompt={(p) => handleSendMessage(p, systemPrompt)} />
          ) : (
            <div className="max-w-4xl mx-auto w-full">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}

              {/* Generating / Loading indicator */}
              {loading && (
                <div
                  data-testid="assistant-message"
                  className="flex justify-start mb-6 w-full animate-fade-in"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-violet-400 shadow-md">
                      <Loader2 size={16} className="animate-spin" />
                    </div>
                    <div className="bg-[#151b2b] border border-slate-800 px-4 py-2.5 rounded-2xl rounded-tl-none text-xs text-slate-400 flex items-center gap-2">
                      <span>Generating response with key failover & cache check...</span>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Chat Input */}
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={loading}
          systemPrompt={systemPrompt}
          onSystemPromptChange={setSystemPrompt}
        />
      </div>
    </div>
  );
};

export default App;
