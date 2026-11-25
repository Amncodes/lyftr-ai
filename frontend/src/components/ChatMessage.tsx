import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { Copy, Check, Sparkles, User, Database, Cpu, Clock, Key, AlertCircle } from 'lucide-react';
import { MessageItem } from '../types';

interface ChatMessageProps {
  message: MessageItem;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';
  const isAssistant = message.role === 'assistant';
  const isError = message.isError;

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="flex justify-end mb-6 w-full animate-fade-in">
        <div className="flex items-start max-w-[85%] md:max-w-[70%] flex-row-reverse gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-violet-600 flex items-center justify-center text-white shadow-md shadow-violet-900/30">
            <User size={16} />
          </div>
          <div className="bg-gradient-to-br from-violet-600 to-indigo-700 text-white px-4 py-3 rounded-2xl rounded-tr-none shadow-lg text-sm leading-relaxed whitespace-pre-wrap">
            {message.content}
          </div>
        </div>
      </div>
    );
  }

  // Assistant message (or error display)
  return (
    <div
      data-testid="assistant-message"
      className="flex justify-start mb-6 w-full animate-fade-in"
    >
      <div className="flex items-start max-w-[95%] md:max-w-[85%] gap-3 w-full">
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white shadow-md ${
          isError ? 'bg-rose-600 shadow-rose-900/30' : 'bg-slate-800 border border-slate-700 shadow-slate-900/30'
        }`}>
          {isError ? <AlertCircle size={16} /> : <Sparkles size={16} className="text-violet-400" />}
        </div>

        <div className="flex-1 flex flex-col gap-2">
          {/* Main Bubble */}
          <div className={`relative px-5 py-4 rounded-2xl rounded-tl-none border shadow-md text-sm leading-relaxed ${
            isError
              ? 'bg-rose-950/40 border-rose-800/60 text-rose-200'
              : 'bg-[#151b2b] border-slate-800/90 text-slate-200'
          }`}>
            <div className="prose prose-invert prose-sm max-w-none break-words">
              {isError ? (
                <div className="font-medium text-rose-300">{message.content}</div>
              ) : (
                <ReactMarkdown>{message.content}</ReactMarkdown>
              )}
            </div>

            {/* Copy button */}
            {!isError && (
              <button
                onClick={handleCopy}
                title="Copy response"
                className="absolute top-3 right-3 p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 transition-colors"
              >
                {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
              </button>
            )}
          </div>

          {/* Mandatory Message Metadata Display */}
          {isAssistant && message.metadata && !isError && (
            <div className="flex flex-wrap items-center gap-2 pt-1 px-1 text-xs">
              {/* Resolution Source */}
              <span
                data-testid="meta-source"
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium border ${
                  message.metadata.resolution_source === 'LLM_CACHE'
                    ? 'bg-emerald-950/60 text-emerald-300 border-emerald-800/60'
                    : 'bg-violet-950/60 text-violet-300 border-violet-800/60'
                }`}
              >
                <Database size={11} />
                {message.metadata.resolution_source}
              </span>

              {/* Model */}
              <span
                data-testid="meta-model"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60"
              >
                <Cpu size={11} className="text-slate-400" />
                {message.metadata.model}
              </span>

              {/* Latency */}
              <span
                data-testid="meta-latency"
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60"
              >
                <Clock size={11} className="text-slate-400" />
                {message.metadata.latency_ms} ms
              </span>

              {/* Input Tokens */}
              <span
                data-testid="meta-input-tokens"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60"
              >
                In: <span className="font-mono text-slate-200">{message.metadata.input_tokens}</span>
              </span>

              {/* Output Tokens */}
              <span
                data-testid="meta-output-tokens"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-slate-800/80 text-slate-300 border border-slate-700/60"
              >
                Out: <span className="font-mono text-slate-200">{message.metadata.output_tokens}</span>
              </span>

              {/* Key ID / Failover Badge */}
              {message.metadata.key_id && (
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-indigo-950/60 text-indigo-300 border border-indigo-800/50">
                  <Key size={11} />
                  {message.metadata.key_id}
                  {message.metadata.fallback_attempts > 0 && (
                    <span className="ml-1 text-[10px] text-amber-300 bg-amber-950/80 px-1 rounded border border-amber-700/60">
                      +{message.metadata.fallback_attempts} fallback
                    </span>
                  )}
                </span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
