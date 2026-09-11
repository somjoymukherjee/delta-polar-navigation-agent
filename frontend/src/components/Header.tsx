import React, { useState } from 'react';
import { 
  Compass, AlertTriangle, Play, RefreshCw, Zap, ShieldAlert, 
  Layers, Radio, Activity, Navigation, CheckCircle2 
} from 'lucide-react';
import { api } from '../services/api';
import type { SystemStatus } from '../services/api';

interface HeaderProps {
  status: SystemStatus | null;
  onRefresh: () => void;
  activeTab: string;
  setActiveTab: (tab: string) => void;
  unreadAlerts: number;
  onOpenAudit: () => void;
  onToggleActivity: () => void;
  isActivityOpen: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  status,
  onRefresh,
  activeTab,
  setActiveTab,
  unreadAlerts,
  onOpenAudit,
  onToggleActivity,
  isActivityOpen
}) => {
  const [simulating, setSimulating] = useState(false);

  const handleSimStep = async (stage: number) => {
    setSimulating(true);
    try {
      await api.stepSimulation(stage);
      onRefresh();
    } finally {
      setSimulating(false);
    }
  };

  const handleCalvingTrigger = async () => {
    setSimulating(true);
    try {
      await api.triggerCalvingEvent();
      onRefresh();
    } finally {
      setSimulating(false);
    }
  };

  const handleReset = async () => {
    setSimulating(true);
    try {
      await api.resetSimulation();
      onRefresh();
    } finally {
      setSimulating(false);
    }
  };

  const handleModeChange = async (mode: string) => {
    await api.setMode(mode);
    onRefresh();
  };

  const currentStep = status?.current_step || 'MONITOR';
  const steps = ['OBSERVE', 'PERCEIVE', 'REASON', 'PLAN', 'ACT', 'MONITOR'];

  return (
    <header className="border-b border-cyan-900/40 bg-polar-900/90 backdrop-blur-md px-4 py-2.5 flex flex-col gap-2">
      {/* Top Bar */}
      <div className="flex items-center justify-between">
        {/* Brand & System Title */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-lg bg-cyan-950/80 border border-cyan-500/50 shadow-lg shadow-cyan-500/20">
            <Compass className="w-6 h-6 text-cyan-400 animate-spin-slow" />
            <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-2xl font-bold tracking-wider text-white flex items-center gap-2">
                DeLTa <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">v2.4-POLAR</span>
              </h1>
              {/* Mode Badge */}
              <select 
                value={status?.mode || 'DEMO'} 
                onChange={(e) => handleModeChange(e.target.value)}
                className="text-xs font-sans font-medium px-2.5 py-1 rounded bg-polar-800 border border-slate-700 text-slate-200 cursor-pointer focus:outline-none focus:border-cyan-400"
              >
                <option value="DEMO">🟡 DEMO MODE (Weddell Digital Twin)</option>
                <option value="LIVE">🔴 LIVE MODE (Open-Meteo & EO Active)</option>
                <option value="HISTORICAL_REPLAY">🔵 HISTORICAL REPLAY (Larsen C 2017)</option>
              </select>
            </div>
            <p className="text-xs text-slate-400 font-sans mt-0.5">
              Dynamic Environmental & Logistics/Navigation Intelligence Agent
            </p>
          </div>
        </div>

        {/* Vessel Telemetry HUD */}
        <div className="hidden lg:flex items-center gap-4 px-3.5 py-1.5 rounded-lg bg-polar-850/80 border border-slate-800 text-sm font-sans">
          <div className="flex items-center gap-1.5">
            <Navigation className="w-4 h-4 text-cyan-400" />
            <span className="text-slate-400">Vessel:</span>
            <span className="text-slate-200 font-semibold">{status?.vessel_name || 'R/V Sir David Attenborough'}</span>
          </div>
          <div className="h-4 w-px bg-slate-800" />
          <div>
            <span className="text-slate-400">Class:</span> <span className="text-emerald-400 font-mono font-bold">{status?.polar_class || 'PC5'}</span>
          </div>
          <div className="h-4 w-px bg-slate-800" />
          <div>
            <span className="text-slate-400">Pos:</span> <span className="text-slate-200 font-mono">{status?.coordinates ? `${Math.abs(status.coordinates[0]).toFixed(2)}°S, ${Math.abs(status.coordinates[1]).toFixed(2)}°W` : '64.82°S, 63.50°W'}</span>
          </div>
        </div>

        {/* Simulation Controls HUD */}
        <div className="flex items-center gap-2 bg-polar-950/80 px-3 py-1.5 rounded-lg border border-slate-800">
          <span className="text-xs font-sans font-medium text-slate-400 flex items-center gap-1">
            <Play className="w-3.5 h-3.5 text-cyan-400" /> SIM TIMELINE:
          </span>
          <button 
            onClick={() => handleSimStep(0)}
            disabled={simulating}
            className={`px-2.5 py-1 text-xs font-sans font-semibold rounded transition-colors ${
              status?.scenario_stage === 0 ? 'bg-cyan-500 text-polar-950 font-bold' : 'bg-polar-800 text-slate-300 hover:bg-polar-750'
            }`}
            title="T+0: Baseline departure from Gerlache Strait"
          >
            T+0 Baseline
          </button>
          <button 
            onClick={() => handleSimStep(1)}
            disabled={simulating}
            className={`px-2.5 py-1 text-xs font-sans font-semibold rounded transition-colors ${
              status?.scenario_stage === 1 ? 'bg-amber-500 text-polar-950 font-bold' : 'bg-polar-800 text-slate-300 hover:bg-polar-750'
            }`}
            title="T+6h: Katabatic storm & pack ice compression"
          >
            T+6h Storm
          </button>
          <button 
            onClick={handleCalvingTrigger}
            disabled={simulating}
            className={`px-3 py-1 text-xs font-sans font-bold rounded transition-all flex items-center gap-1 ${
              status?.scenario_stage === 2 
                ? 'bg-red-500 text-white shadow-lg shadow-red-500/30' 
                : 'bg-red-950/70 border border-red-500/40 text-red-300 hover:bg-red-900/60'
            }`}
            title="Simulate sudden ice-front calving fracture and autonomous route recalculation!"
          >
            <Zap className="w-3.5 h-3.5 text-red-400 animate-bounce" />
            T+12h Calving Event!
          </button>
          <button 
            onClick={handleReset}
            disabled={simulating}
            className="p-1.5 rounded bg-polar-800 text-slate-400 hover:text-white hover:bg-polar-750"
            title="Reset to Baseline"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${simulating ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Autonomous Agent Loop Tracker & Tab Bar */}
      <div className="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/60">
        {/* Visual Agent Loop */}
        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-400 text-xs font-sans uppercase tracking-wider mr-1">Loop State:</span>
          {steps.map((s, idx) => {
            const isCurrent = currentStep === s;
            return (
              <React.Fragment key={s}>
                <span className={`px-2.5 py-0.5 rounded transition-all font-mono text-xs ${
                  isCurrent 
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/60 font-bold shadow-sm shadow-cyan-500/20' 
                    : 'text-slate-500 bg-polar-950/60'
                }`}>
                  {s}
                </span>
                {idx < steps.length - 1 && <span className="text-slate-700">➔</span>}
              </React.Fragment>
            );
          })}
        </div>

        {/* Navigation Tabs (Scaled to 14px text-sm) */}
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setActiveTab('map')}
            className={`px-3 py-1.5 text-sm font-sans rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'map'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-polar-800 font-medium'
            }`}
          >
            <Compass className="w-4 h-4" /> Polar Intelligence Map
          </button>

          <button
            onClick={() => setActiveTab('satellite')}
            className={`px-3 py-1.5 text-sm font-sans rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'satellite'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-polar-800 font-medium'
            }`}
          >
            <Radio className="w-4 h-4" /> Satellite & CV Viewer
          </button>

          <button
            onClick={() => setActiveTab('hazards')}
            className={`px-3 py-1.5 text-sm font-sans rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'hazards'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-polar-800 font-medium'
            }`}
          >
            <Activity className="w-4 h-4" /> Glacier Hazard Explorer
          </button>

          <button
            onClick={() => setActiveTab('alerts')}
            className={`relative px-3 py-1.5 text-sm font-sans rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'alerts'
                ? 'bg-red-500/20 text-red-300 border border-red-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-polar-800 font-medium'
            }`}
          >
            <AlertTriangle className="w-4 h-4 text-amber-400" /> Early Warning Alerts
            {unreadAlerts > 0 && (
              <span className="w-4 h-4 rounded-full bg-red-500 text-white text-[11px] font-mono flex items-center justify-center font-bold">
                {unreadAlerts}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('chat')}
            className={`px-3 py-1.5 text-sm font-sans rounded-md transition-all flex items-center gap-1.5 ${
              activeTab === 'chat'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-semibold'
                : 'text-slate-400 hover:text-slate-200 hover:bg-polar-800 font-medium'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-cyan-400" /> AI Command Center
          </button>

          <div className="h-4 w-px bg-slate-800 mx-1" />

          <button
            onClick={onToggleActivity}
            className={`px-3 py-1.5 text-sm font-sans rounded-md border transition-all flex items-center gap-1.5 ${
              isActivityOpen
                ? 'bg-purple-950/80 border-purple-500/60 text-purple-300 font-bold'
                : 'bg-polar-900 border-slate-800 text-slate-400 hover:text-white font-medium'
            }`}
            title="Toggle Real-Time Operational Agent Activity Stream"
          >
            <Activity className="w-4 h-4 text-purple-400" /> Activity Stream
          </button>

          <button
            onClick={onOpenAudit}
            className="px-3 py-1.5 text-sm font-sans font-medium rounded-md bg-polar-900 border border-slate-800 text-slate-400 hover:text-cyan-300 hover:border-cyan-800 transition-all flex items-center gap-1.5"
            title="Inspect Operator Decision & Traceability Audit Log"
          >
            <ShieldAlert className="w-4 h-4 text-emerald-400" /> Audit Log
          </button>
        </div>
      </div>
    </header>
  );
};
