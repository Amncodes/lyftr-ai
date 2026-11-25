import React, { useState, useRef, useEffect } from 'react';
import { Send, Settings2, ChevronDown, ChevronUp } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, systemPrompt?: string) => void;
  disabled: boolean;
  systemPrompt: string;
  onSystemPromptChange: (val: string) => void;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled,
  systemPrompt,
  onSystemPromptChange,
}) => {
  const [input, setInput] = useState('');
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || disabled) return;
    onSendMessage(trimmed, systemPrompt);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pb-4 pt-1">
      {/* Optional System Prompt Dropdown */}
      <div className="mb-2">
        <button
          type="button"
          onClick={() => setShowSystemPrompt(!showSystemPrompt)}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors py-1 px-2 rounded-lg hover:bg-slate-800/60"
        >
          <Settings2 size={13} />
          <span>System Prompt Configuration</span>
          {showSystemPrompt ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
          {systemPrompt.trim() && (
            <span className="w-2 h-2 rounded-full bg-violet-400" />
          )}
        </button>

        {showSystemPrompt && (
          <div className="mt-1.5 p-3 rounded-xl bg-slate-900/90 border border-slate-800 shadow-lg animate-fade-in">
            <label className="block text-[11px] font-medium text-slate-400 mb-1">
              Custom System Instructions (Not exposed in public history)
            </label>
            <input
              type="text"
              data-testid="system-prompt-input"
              value={systemPrompt}
              onChange={(e) => onSystemPromptChange(e.target.value)}
              placeholder="e.g. You are a helpful software engineering assistant."
              className="w-full bg-[#141a29] border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-violet-500"
            />
          </div>
        )}
      </div>

      {/* Main Input Form */}
      <form
        onSubmit={handleSubmit}
        className="relative bg-[#141a29] border border-slate-800/90 focus-within:border-violet-500/80 rounded-2xl shadow-xl transition-all"
      >
        <textarea
          ref={textareaRef}
          data-testid="chat-input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={disabled}
          placeholder="Ask a question or enter a prompt... (Shift+Enter for newline)"
          rows={1}
          className="w-full bg-transparent text-slate-100 placeholder-slate-500 text-sm px-4 py-3.5 pr-14 focus:outline-none resize-none max-h-40 leading-relaxed disabled:opacity-50"
        />

        <button
          type="submit"
          data-testid="send-button"
          disabled={disabled || !input.trim()}
          className="absolute right-2.5 bottom-2.5 p-2 rounded-xl bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:hover:bg-violet-600 text-white shadow-md shadow-violet-900/40 transition-all flex items-center justify-center active:scale-95"
        >
          <Send size={16} />
        </button>
      </form>
    </div>
  );
};
