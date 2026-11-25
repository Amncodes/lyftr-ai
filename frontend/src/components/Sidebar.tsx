import React, { useState } from 'react';
import { Plus, MessageSquare, ShieldCheck, Zap, Copy, Check, SlidersHorizontal } from 'lucide-react';
import { HealthStatus } from '../types';

interface SidebarProps {
  sessionId: string;
  onNewChat: () => void;
  health: HealthStatus | null;
  simFailure: string;
  onSimFailureChange: (val: string) => void;
  mobileOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessionId,
  onNewChat,
  health,
  simFailure,
  onSimFailureChange,
  mobileOpen,
  onCloseMobile,
}) => {
  const [copied, setCopied] = useState(false);

  const copySession = () => {
    navigator.clipboard.writeText(sessionId);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-30 md:hidden backdrop-blur-sm"
          onClick={onCloseMobile}
        />
      )}

      <aside
        className={`fixed md:static inset-y-0 left-0 z-40 w-72 bg-[#0d121f] border-r border-slate-800 flex flex-col transition-transform duration-300 ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-violet-600 to-indigo-500 flex items-center justify-center text-white shadow-md shadow-violet-900/40 font-bold text-lg">
              L
            </div>
            <div>
              <div className="font-semibold text-slate-100 text-sm tracking-tight flex items-center gap-1.5">
                Lyftr AI
                <span className="text-[10px] bg-violet-950 text-violet-300 border border-violet-800/60 px-1.5 py-0.2 rounded font-mono">
                  v1.0
                </span>
              </div>
              <div className="text-[11px] text-slate-400">Resilient LLM Gateway</div>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={() => {
              onNewChat();
              onCloseMobile();
            }}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-violet-600 hover:bg-violet-500 text-white font-medium text-sm transition-all shadow-md shadow-violet-900/30 active:scale-[0.98]"
          >
            <Plus size={16} />
            New Chat
          </button>
        </div>

        {/* Current Session Indicator */}
        <div className="px-4 py-2">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2">
            Current Session
          </div>
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 flex items-center justify-between">
            <div className="flex items-center gap-2 overflow-hidden">
              <MessageSquare size={16} className="text-violet-400 flex-shrink-0" />
              <span className="text-xs font-mono text-slate-300 truncate" title={sessionId}>
                {sessionId}
              </span>
            </div>
            <button
              onClick={copySession}
              title="Copy Session ID"
              className="text-slate-400 hover:text-slate-200 p-1 rounded transition-colors"
            >
              {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
            </button>
          </div>
        </div>

        {/* Failure Simulation Test Hook Control */}
        <div className="px-4 py-3">
          <div className="text-xs uppercase tracking-wider text-slate-400 font-semibold mb-2 flex items-center gap-1.5">
            <SlidersHorizontal size={13} className="text-slate-400" />
            Failure Simulation Hook
          </div>
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-3 space-y-2">
            <div className="text-[11px] text-slate-400 leading-snug">
              Header <code className="text-violet-300">X-Simulate-Failure</code>:
            </div>
            <select
              value={simFailure}
              onChange={(e) => onSimFailureChange(e.target.value)}
              className="w-full bg-[#141a29] border border-slate-700 rounded-lg text-xs text-slate-200 px-2.5 py-1.5 focus:outline-none focus:border-violet-500"
            >
              <option value="">None (Normal execution)</option>
              <option value="key_1=429">key_1=429 (Fallback to key_2)</option>
              <option value="key_1=500">key_1=500 (Fallback to key_2)</option>
              <option value="key_1=429,key_2=500">key_1=429,key_2=500 (503 fail)</option>
              <option value="*=429">*=429 (All keys 429 -&gt; 503)</option>
            </select>
          </div>
        </div>

        <div className="flex-1" />

        {/* System Health / Status Indicator */}
        <div className="p-4 border-t border-slate-800/80 bg-slate-900/40">
          <div className="flex items-center justify-between text-xs mb-2">
            <span className="text-slate-400 font-medium flex items-center gap-1.5">
              <span
                className={`w-2 h-2 rounded-full ${
                  health?.status === 'ok' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'
                }`}
              />
              System Status
            </span>
            <span className={`font-mono text-[11px] ${
              health?.status === 'ok' ? 'text-emerald-400' : 'text-rose-400'
            }`}>
              {health?.status === 'ok' ? 'ONLINE' : 'DEGRADED'}
            </span>
          </div>

          <div className="space-y-1.5 text-[11px] text-slate-400">
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-slate-400">
                <ShieldCheck size={12} className="text-slate-400" />
                Configured Keys
              </span>
              <span className="font-mono text-slate-200 bg-slate-800 px-1.5 py-0.5 rounded">
                {health?.keys_configured ?? 0} active
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="flex items-center gap-1.5 text-slate-400">
                <Zap size={12} className="text-slate-400" />
                LiteLLM Cache
              </span>
              <span className={`font-mono px-1.5 py-0.5 rounded ${
                health?.cache_enabled ? 'text-emerald-300 bg-emerald-950/60' : 'text-slate-400 bg-slate-800'
              }`}>
                {health?.cache_enabled ? 'ENABLED' : 'DISABLED'}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
};
