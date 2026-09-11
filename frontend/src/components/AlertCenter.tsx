import React, { useState } from 'react';
import { 
  AlertTriangle, ShieldAlert, CheckCircle2, Clock, MapPin, 
  HelpCircle, Compass, ShieldCheck, Check, UserCheck 
} from 'lucide-react';
import { api } from '../services/api';
import type { Alert } from '../services/api';

interface AlertCenterProps {
  alerts: Alert[];
  onAcknowledge: (alertId: string) => void;
  onFocusCoordinates?: (coords: [number, number]) => void;
}

export const AlertCenter: React.FC<AlertCenterProps> = ({
  alerts,
  onAcknowledge,
  onFocusCoordinates
}) => {
  const [filter, setFilter] = useState<string>('ALL');
  const [ackLoading, setAckLoading] = useState<string | null>(null);

  const filteredAlerts = alerts?.filter(a => {
    if (filter === 'ALL') return true;
    return a.severity === filter;
  }) || [];

  const handleAck = async (alertId: string) => {
    setAckLoading(alertId);
    try {
      await api.acknowledgeAlert(alertId, 'DUTY_OFFICER');
      onAcknowledge(alertId);
    } finally {
      setAckLoading(null);
    }
  };

  const getSeverityStyle = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return { badge: 'bg-red-500 text-white animate-pulse', border: 'border-red-500/60', bg: 'bg-red-950/30' };
      case 'WARNING':
        return { badge: 'bg-amber-500 text-polar-950 font-bold', border: 'border-amber-500/50', bg: 'bg-amber-950/20' };
      case 'ADVISORY':
        return { badge: 'bg-cyan-500 text-polar-950 font-bold', border: 'border-cyan-500/40', bg: 'bg-cyan-950/20' };
      case 'WATCH':
        return { badge: 'bg-blue-600 text-white', border: 'border-blue-500/40', bg: 'bg-blue-950/20' };
      default:
        return { badge: 'bg-slate-700 text-slate-200', border: 'border-slate-800', bg: 'bg-polar-900' };
    }
  };

  return (
    <div className="w-full h-[calc(100vh-102px)] p-4 flex flex-col gap-4 overflow-y-auto font-sans text-sm">
      {/* Header & Filter Bar */}
      <div className="glass-panel p-4 rounded-xl border border-cyan-900/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-5 h-5 text-red-400" />
            <h2 className="text-lg font-bold text-white">
              DeLTa Early-Warning & Cryosphere Alert Center
            </h2>
            <span className="text-xs font-mono px-2.5 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-bold">
              {alerts?.length || 0} ACTIVE ALERTS
            </span>
          </div>
          <p className="text-slate-300 text-sm mt-1">
            Real-time hazard alerts formatted using strict 7-part operational early-warning schema.
          </p>
        </div>

        {/* Severity Filter Pills */}
        <div className="flex items-center gap-1.5">
          {['ALL', 'CRITICAL', 'WARNING', 'ADVISORY', 'WATCH'].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilter(sev)}
              className={`px-3.5 py-1.5 rounded-md transition-all font-sans text-sm font-medium ${
                filter === sev
                  ? 'bg-cyan-500 text-polar-950 font-bold shadow-md shadow-cyan-500/20'
                  : 'bg-polar-900 text-slate-400 border border-slate-800 hover:text-white'
              }`}
            >
              {sev}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Grid */}
      <div className="flex flex-col gap-4">
        {filteredAlerts.length === 0 ? (
          <div className="glass-panel p-12 rounded-xl text-center text-slate-400">
            <ShieldCheck className="w-10 h-10 text-emerald-400 mx-auto mb-2" />
            <p className="text-base font-bold text-white">No Active Alerts</p>
            <p className="text-sm text-slate-400 mt-1">Environmental telemetry across all monitored sectors is nominal.</p>
          </div>
        ) : (
          filteredAlerts.map((alert: Alert) => {
            const styles = getSeverityStyle(alert.severity);

            return (
              <div
                key={alert.alert_id}
                className={`p-4 rounded-xl border ${styles.border} ${styles.bg} glass-panel flex flex-col gap-3.5 transition-all`}
              >
                {/* Header Row */}
                <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-slate-800">
                  <div className="flex items-center gap-2.5">
                    <span className={`px-2.5 py-1 rounded text-xs font-bold font-sans ${styles.badge}`}>
                      {alert.severity}
                    </span>
                    <span className="font-bold text-white text-base">{alert.what}</span>
                  </div>

                  <div className="flex items-center gap-2">
                    {onFocusCoordinates && (
                      <button
                        onClick={() => onFocusCoordinates([alert.where_lat, alert.where_lon])}
                        className="px-3 py-1.5 rounded bg-polar-900 border border-cyan-800/60 text-cyan-300 hover:bg-cyan-950 flex items-center gap-1.5 text-xs font-sans font-semibold"
                        title="Jump to coordinates on map"
                      >
                        <Compass className="w-4 h-4" /> Focus Map
                      </button>
                    )}

                    {!alert.acknowledged ? (
                      <button
                        onClick={() => handleAck(alert.alert_id)}
                        disabled={ackLoading === alert.alert_id}
                        className="px-3 py-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 flex items-center gap-1.5 text-xs font-sans font-medium"
                      >
                        <Check className="w-4 h-4 text-emerald-400" /> Acknowledge
                      </button>
                    ) : (
                      <span className="text-xs font-sans text-emerald-400 flex items-center gap-1.5 px-2.5 py-1 rounded bg-emerald-950/60 border border-emerald-800">
                        <UserCheck className="w-3.5 h-3.5" /> Acknowledged by {alert.acknowledged_by || 'Officer'}
                      </span>
                    )}
                  </div>
                </div>

                {/* 7-Part Schema Breakdown Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
                  <div className="p-3 rounded-lg bg-polar-950/70 border border-slate-850">
                    <span className="text-slate-400 uppercase tracking-wider block text-[11px] font-sans font-bold mb-0.5">Where:</span>
                    <span className="text-slate-100 font-semibold text-sm">{alert.where_location_name}</span>
                    <span className="text-slate-400 font-mono text-xs block mt-1">({alert.where_lat}°S, {alert.where_lon}°W)</span>
                  </div>

                  <div className="p-3 rounded-lg bg-polar-950/70 border border-slate-850">
                    <span className="text-slate-400 uppercase tracking-wider block text-[11px] font-sans font-bold mb-0.5">When:</span>
                    <span className="text-slate-200 font-mono text-sm font-medium">{new Date(alert.when_timestamp).toLocaleTimeString()} UTC</span>
                    <span className="text-slate-400 text-xs block mt-1">Automated SAR Radar Pass</span>
                  </div>

                  <div className="p-3 rounded-lg bg-polar-950/70 border border-slate-850">
                    <span className="text-slate-400 uppercase tracking-wider block text-[11px] font-sans font-bold mb-0.5">AI Confidence:</span>
                    <span className="text-emerald-400 font-mono font-bold text-base">{(alert.confidence * 100).toFixed(0)}%</span>
                    <span className="text-slate-400 text-xs block mt-1">Multi-Sensor Validation</span>
                  </div>

                  <div className="p-3 rounded-lg bg-polar-950/70 border border-slate-850">
                    <span className="text-slate-400 uppercase tracking-wider block text-[11px] font-sans font-bold mb-0.5">Alert ID:</span>
                    <span className="text-cyan-300 font-mono font-bold text-xs">{alert.alert_id}</span>
                    <span className="text-slate-400 text-xs block mt-1">Audit Log Enforced</span>
                  </div>
                </div>

                {/* Evidence & Development (Target 14-15px text-sm) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
                  <div className="p-3 rounded-lg bg-polar-950/50 border border-slate-800">
                    <span className="text-slate-400 block text-xs font-sans font-bold uppercase tracking-wider mb-1.5">
                      Scientific Evidence & Observation:
                    </span>
                    <p className="text-slate-200 font-sans leading-relaxed text-sm">{alert.evidence}</p>
                  </div>

                  <div className="p-3 rounded-lg bg-polar-950/50 border border-slate-800">
                    <span className="text-slate-400 block text-xs font-sans font-bold uppercase tracking-wider mb-1.5">
                      Expected Development:
                    </span>
                    <p className="text-slate-200 font-sans leading-relaxed text-sm">{alert.expected_development}</p>
                  </div>
                </div>

                {/* Recommended Operator Action */}
                <div className="p-3.5 rounded-lg bg-cyan-950/40 border border-cyan-500/40 text-cyan-200 flex items-start gap-2.5 text-sm font-sans">
                  <ShieldCheck className="w-5 h-5 text-cyan-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-bold text-white block text-sm mb-0.5">Recommended Operator Action:</span>
                    <span className="leading-relaxed text-sm text-cyan-100">{alert.recommended_action}</span>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
