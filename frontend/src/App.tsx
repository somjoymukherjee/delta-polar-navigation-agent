import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { PolarMap } from './components/PolarMap';
import { SatelliteViewer } from './components/SatelliteViewer';
import { GlacierExplorer } from './components/GlacierExplorer';
import { AlertCenter } from './components/AlertCenter';
import { AgentChat } from './components/AgentChat';
import { AuditLogModal } from './components/AuditLogModal';
import { ActivityStreamPanel } from './components/ActivityStreamPanel';
import { api } from './services/api';
import type { SystemStatus, VoyagePlan, Alert, ChatMessage } from './services/api';
import { ShieldCheck, Radio, Database, Activity, Sparkles } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('map');
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [voyagePlan, setVoyagePlan] = useState<VoyagePlan | null>(null);
  const [features, setFeatures] = useState<any>(null);
  const [riskGrid, setRiskGrid] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [passes, setPasses] = useState<any[]>([]);
  const [temporalChange, setTemporalChange] = useState<any>(null);
  const [glaciers, setGlaciers] = useState<any[]>([]);
  const [activities, setActivities] = useState<any[]>([]);
  const [riskDelta, setRiskDelta] = useState<any>(null);
  const [sharedState, setSharedState] = useState<any>(null);
  const [focusedCoords, setFocusedCoords] = useState<[number, number] | null>(null);
  const [isAuditOpen, setIsAuditOpen] = useState<boolean>(false);
  const [isActivityOpen, setIsActivityOpen] = useState<boolean>(false);

  const fetchAllData = async () => {
    try {
      const [
        s, vp, feat, rg, al, ch, ps, tc, gl, act, rd, ss
      ] = await Promise.all([
        api.getStatus().catch(e => { console.warn("status err", e); return null; }),
        api.getRoutes().catch(e => { console.warn("routes err", e); return null; }),
        api.getSatelliteFeatures().catch(e => { console.warn("features err", e); return null; }),
        api.getRiskGrid().catch(() => []),
        api.getAlerts().catch(() => []),
        api.getChatHistory().catch(() => []),
        api.getSatellitePasses().catch(() => []),
        api.getTemporalChange().catch(() => null),
        api.getGlaciers().catch(() => []),
        api.getAgentActivity().catch(() => []),
        api.getRiskDelta().catch(() => null),
        api.getSharedState().catch(() => null)
      ]);

      if (s) setStatus(s);
      if (vp) setVoyagePlan(vp);
      if (feat) setFeatures(feat);
      if (rg) setRiskGrid(rg);
      if (al) setAlerts(al);
      if (ch) setChatHistory(ch);
      if (ps) setPasses(ps);
      if (tc) setTemporalChange(tc);
      if (gl) setGlaciers(gl);
      if (act) setActivities(act);
      if (rd) setRiskDelta(rd);
      if (ss) setSharedState(ss);
    } catch (err) {
      console.error("Failed fetching DeLTa telemetry:", err);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 10000); // 10s auto-refresh
    return () => clearInterval(interval);
  }, []);

  const handleSendMessage = async (text: string) => {
    // Optimistic user update
    const tempUserMsg: ChatMessage = {
      id: `USER-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date().toISOString()
    };
    setChatHistory(prev => [...prev, tempUserMsg]);

    try {
      const reply = await api.sendChatMessage(text);
      setChatHistory(prev => [...prev.filter(m => m.id !== tempUserMsg.id), tempUserMsg, reply]);
      fetchAllData();
    } catch (e) {
      console.error("Chat error:", e);
    }
  };

  const handleAlertAcknowledge = (alertId: string) => {
    setAlerts(prev => prev.map(a => a.alert_id === alertId ? { ...a, acknowledged: true } : a));
  };

  const handleFocusCoordinates = (coords: [number, number]) => {
    setFocusedCoords(coords);
    setActiveTab('map');
  };

  const unreadAlerts = alerts?.filter(a => !a.acknowledged && (a.severity === 'CRITICAL' || a.severity === 'WARNING')).length || 0;

  return (
    <div className="flex flex-col w-full h-screen bg-polar-950 text-slate-100 overflow-hidden relative">
      {/* Operational Header HUD */}
      <Header
        status={status}
        onRefresh={fetchAllData}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        unreadAlerts={unreadAlerts}
        onOpenAudit={() => setIsAuditOpen(true)}
        onToggleActivity={() => setIsActivityOpen(prev => !prev)}
        isActivityOpen={isActivityOpen}
      />

      {/* Main View Area */}
      <main className="flex-1 relative w-full h-[calc(100vh-102px)] overflow-hidden">
        {activeTab === 'map' && (
          <PolarMap
            voyagePlan={voyagePlan}
            features={features}
            riskGrid={riskGrid}
            focusedCoordinates={focusedCoords}
            onRefresh={fetchAllData}
          />
        )}

        {activeTab === 'satellite' && (
          <SatelliteViewer
            temporalChange={temporalChange}
            passes={passes}
          />
        )}

        {activeTab === 'hazards' && (
          <GlacierExplorer
            glaciers={glaciers}
          />
        )}

        {activeTab === 'alerts' && (
          <AlertCenter
            alerts={alerts}
            onAcknowledge={handleAlertAcknowledge}
            onFocusCoordinates={handleFocusCoordinates}
          />
        )}

        {activeTab === 'chat' && (
          <AgentChat
            chatHistory={chatHistory}
            onSendMessage={handleSendMessage}
            onRefresh={fetchAllData}
          />
        )}

        {/* Floating Data Quality & Freshness HUD Card (Driven by SharedSystemState) */}
        <div className="absolute bottom-4 left-4 z-20 glass-panel bg-polar-950/90 border border-slate-800 rounded-lg p-3 text-xs font-sans shadow-xl hidden sm:flex items-center gap-3.5">
          <div className="flex items-center gap-1.5 text-cyan-300">
            <Radio className="w-4 h-4 text-cyan-400" />
            <span className="font-bold">{sharedState?.provenance?.source || 'Sentinel-1/2 SAR Fusion'}</span>
          </div>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">
            Obs: <strong className="text-white font-mono">{sharedState?.data_freshness_seconds ? `${Math.round(sharedState.data_freshness_seconds)}s ago` : '12s ago'}</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">
            Quality: <strong className="text-emerald-400 font-mono">{sharedState?.provenance?.quality_status || 'OPTIMAL'}</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className="text-slate-300">
            Confidence: <strong className="text-cyan-300 font-mono">{Math.round((sharedState?.overall_confidence ?? 0.94) * 100)}%</strong>
          </span>
          <span className="text-slate-600">|</span>
          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
            (status?.mode || sharedState?.mode) === 'LIVE' ? 'bg-red-950 text-red-300 border border-red-800' : 'bg-amber-950 text-amber-300 border border-amber-800'
          }`}>
            {status?.mode || sharedState?.mode || 'DEMO'}
          </span>
        </div>

        {/* Collapsible Operational Agent Activity Stream (Point 22) */}
        {isActivityOpen && (
          <div className="absolute top-4 right-4 z-30 w-96 shadow-2xl animate-in slide-in-from-right duration-200">
            <ActivityStreamPanel
              activities={activities}
              onRefresh={fetchAllData}
            />
          </div>
        )}
      </main>

      {/* Audit Log Modal (Points 18 & 23) */}
      <AuditLogModal
        isOpen={isAuditOpen}
        onClose={() => setIsAuditOpen(false)}
      />

      {/* Bottom Status Bar */}
      <footer className="h-7 bg-polar-900 border-t border-slate-800/80 px-4 flex items-center justify-between text-xs font-sans text-slate-300 select-none z-20">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 text-emerald-400 font-semibold">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            AGENT LOOP: <strong className="font-mono text-emerald-300">{status?.current_step || 'MONITOR'}</strong>
          </span>
          <span className="text-slate-700">|</span>
          <span>Scenario: <strong className="text-slate-200 font-mono">{status?.scenario_step_name || 'T+0 Baseline'}</strong></span>
          <span className="text-slate-700">|</span>
          <span>Data Ingestion: <strong className="text-cyan-300 font-sans">Synchronized (SAR + Optical + Marine)</strong></span>
        </div>

        <div className="flex items-center gap-4">
          <span>Active Route: <strong className="text-cyan-300 font-mono">{voyagePlan?.recommended_route?.name || 'Route Alpha'}</strong></span>
          <span className="text-slate-700">|</span>
          <span className="text-slate-400 font-sans">DeLTa Cryosphere Decision-Support System</span>
        </div>
      </footer>
    </div>
  );
};

export default App;
