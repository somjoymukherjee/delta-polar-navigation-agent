import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, Bot, User, Sparkles, CheckCircle2, ShieldAlert, 
  HelpCircle, Wrench, ShieldCheck, ArrowRight, CornerDownLeft 
} from 'lucide-react';
import { api } from '../services/api';
import type { ChatMessage } from '../services/api';

interface AgentChatProps {
  chatHistory: ChatMessage[];
  onSendMessage: (text: string) => void;
  onRefresh: () => void;
}

export const AgentChat: React.FC<AgentChatProps> = ({
  chatHistory,
  onSendMessage,
  onRefresh
}) => {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatHistory]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    const msg = input;
    setInput('');
    onSendMessage(msg);
  };

  const [isSubmittingRoute, setIsSubmittingRoute] = useState(false);

  const handleQuickPrompt = (prompt: string) => {
    onSendMessage(prompt);
  };

  const handleAcceptRoute = async () => {
    if (isSubmittingRoute) return;
    setIsSubmittingRoute(true);
    try {
      await api.logAuditAction(
        'ACCEPT_ROUTE',
        'ROUTE_BALANCED',
        'Master confirmed acceptance of AI-recommended route Alpha.',
        { action: 'ACCEPT_RECOMMENDED_ROUTE' }
      );
      onSendMessage("I have accepted the recommended route. Please update IBS navigation autopilot.");
      onRefresh();
    } catch (err) {
      console.error("Failed to accept route:", err);
    } finally {
      setIsSubmittingRoute(false);
    }
  };

  return (
    <div className="w-full h-[calc(100vh-102px)] p-4 flex flex-col gap-4 font-sans text-sm max-w-5xl mx-auto">
      {/* Top Banner */}
      <div className="glass-panel p-4 rounded-xl border border-cyan-900/40 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-cyan-950 border border-cyan-500/50 flex items-center justify-center text-cyan-400 shadow-md shrink-0">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              DeLTa AI Command & Reasoning Engine
            </h2>
            <p className="text-xs text-slate-300 mt-0.5">
              Stateful tool-calling agent reasoning over satellite SAR, kinematics, and polar maritime safety.
            </p>
          </div>
        </div>

        {/* Quick Suggestion Chips */}
        <div className="hidden md:flex items-center gap-1.5 flex-wrap max-w-md justify-end">
          {[
            "Why did you change the route?",
            "Scan hazards around ship",
            "Show satellite observation",
            "What is the glacier acceleration?"
          ].map((prompt, i) => (
            <button
              key={i}
              onClick={() => handleQuickPrompt(prompt)}
              className="px-2.5 py-1 rounded bg-polar-900 hover:bg-polar-800 text-xs text-cyan-300 border border-slate-800 transition-all hover:border-cyan-500/40 font-sans font-medium"
            >
              {prompt}
            </button>
          ))}
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 glass-panel p-4 rounded-xl border border-slate-800 overflow-y-auto space-y-4">
        {chatHistory.map((msg: ChatMessage) => {
          const isUser = msg.role === 'user';

          return (
            <div
              key={msg.id}
              className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
            >
              {!isUser && (
                <div className="w-8 h-8 rounded-lg bg-cyan-950 border border-cyan-500/40 flex items-center justify-center text-cyan-300 shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`max-w-2xl rounded-xl p-4 space-y-2.5 ${
                  isUser
                    ? 'bg-cyan-600 text-white shadow-md'
                    : 'bg-polar-900 border border-slate-800 text-slate-100'
                }`}
              >
                {/* Tool Calling Badges */}
                {msg.tool_calls && msg.tool_calls.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pb-2 border-b border-slate-800 text-xs">
                    <span className="text-slate-400 flex items-center gap-1 font-sans">
                      <Wrench className="w-3.5 h-3.5 text-cyan-400" /> Executed System Tools:
                    </span>
                    {msg.tool_calls.map((t, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 rounded bg-polar-950 text-cyan-300 border border-cyan-800/60 font-mono text-xs"
                      >
                        {t.tool}()
                      </span>
                    ))}
                  </div>
                )}

                {/* Message Body with Markdown formatting support */}
                <div className="text-sm leading-relaxed whitespace-pre-wrap font-sans">
                  {msg.content}
                </div>

                {/* Decision Card (if present) */}
                {msg.decision_card && (
                  <div className="mt-3 p-4 rounded-lg bg-polar-950 border border-cyan-500/40 text-sm font-sans space-y-2.5">
                    <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                      <span className="font-bold text-cyan-300 text-base flex items-center gap-2">
                        <ShieldCheck className="w-4 h-4 text-cyan-400" />
                        {msg.decision_card.decision}
                      </span>
                      <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold">
                        {msg.decision_card.confidence_pct}% AI Confidence
                      </span>
                    </div>

                    {/* Primary Evidence */}
                    <div>
                      <span className="text-xs text-slate-400 uppercase tracking-wider block font-bold mb-1.5">
                        Primary Evidence:
                      </span>
                      <ul className="space-y-1.5">
                        {msg.decision_card.primary_evidence?.map((ev: string, idx: number) => (
                          <li key={idx} className="flex items-start gap-2 text-slate-200 text-sm leading-relaxed">
                            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                            <span>{ev}</span>
                          </li>
                        ))}
                      </ul>
                    </div>

                    {/* Trade-off summary */}
                    <div className="p-2.5 rounded bg-polar-900 border border-slate-800 text-sm text-slate-200 leading-relaxed">
                      <span className="text-slate-400 font-bold block text-xs mb-0.5">Trade-Off:</span>
                      {msg.decision_card.trade_off}
                    </div>

                    {/* Human-in-the-Loop Operator Actions */}
                    <div className="pt-2.5 border-t border-slate-800 flex items-center justify-between gap-2.5">
                      <button
                        onClick={handleAcceptRoute}
                        disabled={isSubmittingRoute}
                        className="px-3.5 py-2 rounded-md bg-emerald-500 text-polar-950 font-bold hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-1.5 text-sm font-sans"
                      >
                        <CheckCircle2 className="w-4 h-4" /> Accept Route Recommendation
                      </button>
                      <button
                        onClick={() => handleQuickPrompt("Why not Route Bravo?")}
                        className="px-3 py-2 rounded-md bg-polar-900 border border-slate-700 text-slate-300 hover:text-white text-sm font-sans font-medium"
                      >
                        Compare Alternatives
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {isUser && (
                <div className="w-8 h-8 rounded-lg bg-cyan-600 flex items-center justify-center text-white shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </div>
          );
        })}
        <div ref={messagesEndRef} />
      </div>

      {/* Message Input Box */}
      <form onSubmit={handleSubmit} className="flex gap-2.5">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask DeLTa: 'Why did you change the route?', 'Assess iceberg risk'..."
          className="flex-1 bg-polar-900 border border-slate-800 rounded-xl px-4 py-3 text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-400 font-sans text-sm"
        />
        <button
          type="submit"
          disabled={!input.trim()}
          className="px-6 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-polar-950 font-bold transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2 font-sans text-sm"
        >
          <span>Send</span>
          <CornerDownLeft className="w-4 h-4" />
        </button>
      </form>
    </div>
  );
};
