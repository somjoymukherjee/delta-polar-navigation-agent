import React from 'react';
import { Activity, Clock, ShieldAlert, Radio, Compass, RefreshCw } from 'lucide-react';

interface ActivityStreamProps {
  activities: any[];
  onRefresh?: () => void;
}

export const ActivityStreamPanel: React.FC<ActivityStreamProps> = ({ activities, onRefresh }) => {
  const getStepColor = (step: string) => {
    switch (step) {
      case 'OBSERVE': return 'bg-blue-950 text-blue-300 border-blue-800';
      case 'PERCEIVE': return 'bg-cyan-950 text-cyan-300 border-cyan-800';
      case 'COMPARE': return 'bg-purple-950 text-purple-300 border-purple-800';
      case 'REASON': return 'bg-indigo-950 text-indigo-300 border-indigo-800';
      case 'PLAN': return 'bg-emerald-950 text-emerald-300 border-emerald-800';
      case 'ACT': return 'bg-amber-950 text-amber-300 border-amber-800';
      case 'ALERT': return 'bg-red-950 text-red-300 border-red-800 animate-pulse';
      case 'MONITOR': return 'bg-slate-900 text-slate-400 border-slate-800';
      default: return 'bg-slate-900 text-slate-400 border-slate-800';
    }
  };

  return (
    <div className="glass-panel rounded-xl border border-slate-800 p-4 flex flex-col gap-3 font-sans text-sm max-h-80 overflow-hidden">
      <div className="flex items-center justify-between pb-2.5 border-b border-slate-800">
        <span className="font-bold text-cyan-300 flex items-center gap-2 text-sm">
          <Activity className="w-4 h-4 text-cyan-400" /> Operational Agent Activity Stream
        </span>
        <div className="flex items-center gap-2 text-xs text-slate-300 font-sans font-medium">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
          <span>LIVE EVENTS</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-2 pr-1">
        {activities?.length === 0 ? (
          <div className="text-center py-6 text-slate-400 text-xs font-sans">Awaiting system events...</div>
        ) : (
          activities.slice().reverse().map((act: any) => (
            <div
              key={act.id}
              className="p-2.5 rounded-lg bg-polar-950/80 border border-slate-850 flex items-start gap-2.5 hover:border-slate-700 transition-colors"
            >
              <span className="font-mono text-slate-400 text-xs shrink-0 font-medium mt-0.5">
                {act.time_display}
              </span>

              <span className={`font-mono px-2 py-0.5 rounded text-xs font-bold border uppercase shrink-0 ${getStepColor(act.step)}`}>
                {act.step}
              </span>

              <div className="flex-1 min-w-0">
                <p className="font-sans text-slate-100 text-xs leading-relaxed break-words">{act.action}</p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
