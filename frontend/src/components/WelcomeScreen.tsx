import React from 'react';
import { Sparkles, Zap, ShieldAlert, Cpu } from 'lucide-react';

interface WelcomeScreenProps {
  onSelectPrompt: (prompt: string) => void;
}

export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onSelectPrompt }) => {
  const suggestions = [
    {
      icon: <Sparkles size={16} className="text-violet-400" />,
      title: "What is the capital of France?",
      desc: "Test single-turn live inference and LiteLLM response caching.",
    },
    {
      icon: <Zap size={16} className="text-emerald-400" />,
      title: "Explain the difference between synchronous and asynchronous code.",
      desc: "Observe per-request token usage and response latency.",
    },
    {
      icon: <ShieldAlert size={16} className="text-amber-400" />,
      title: "Write a quick Python script to calculate Fibonacci numbers.",
      desc: "Multi-turn context preserved in SQLite session storage.",
    },
    {
      icon: <Cpu size={16} className="text-indigo-400" />,
      title: "How does LiteLLM key failover prevent downtime?",
      desc: "Simulate HTTP 429/500 to observe automatic key fallback.",
    },
  ];

  return (
    <div className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-2xl mx-auto animate-fade-in">
      <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-xl shadow-violet-900/40 mb-5">
        <Sparkles size={28} />
      </div>

      <h1 className="text-2xl md:text-3xl font-bold text-slate-100 tracking-tight mb-2">
        How can I help you today?
      </h1>
      <p className="text-sm text-slate-400 mb-8 max-w-md">
        Lyftr AI LLM Gateway provides automatic multi-key failover, persistent LiteLLM response caching, and session memory.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full text-left">
        {suggestions.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(item.title)}
            className="p-3.5 rounded-xl bg-[#141a29]/90 hover:bg-[#1a2136] border border-slate-800/80 hover:border-violet-500/50 transition-all text-left group"
          >
            <div className="flex items-center gap-2 mb-1">
              {item.icon}
              <span className="text-xs font-semibold text-slate-200 group-hover:text-violet-300 transition-colors">
                {item.title}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-normal pl-6">
              {item.desc}
            </p>
          </button>
        ))}
      </div>
    </div>
  );
};
