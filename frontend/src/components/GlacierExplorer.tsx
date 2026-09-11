import React, { useState } from 'react';
import { 
  Activity, AlertTriangle, ShieldAlert, Waves, TrendingUp, 
  Clock, ShieldCheck, ChevronRight, CheckCircle2, ArrowUpRight 
} from 'lucide-react';
import { FALLBACK_GLACIERS } from '../services/fallbackData';

interface GlacierExplorerProps {
  glaciers: any[];
}

export const GlacierExplorer: React.FC<GlacierExplorerProps> = ({ glaciers }) => {
  const effectiveGlaciers = (glaciers && glaciers.length > 0) ? glaciers : FALLBACK_GLACIERS;
  const [selectedGlacierId, setSelectedGlacierId] = useState<string>('GLACIER_LARSEN_C_FRONT');

  const activeGlacier = effectiveGlaciers.find(g => g.glacier_id === selectedGlacierId) || effectiveGlaciers[0];

  const accelStatus = String(activeGlacier?.acceleration_status || activeGlacier?.calving_activity || 'BASELINE_EQUILIBRIUM');
  const isCritical = accelStatus.toUpperCase().includes('CRITICAL') || accelStatus.toUpperCase().includes('SURGE');

  const velMPerDay = activeGlacier?.velocity_m_per_day ?? 2.4;
  const velKmYr = activeGlacier?.velocity_km_per_year ?? ((velMPerDay * 365.25) / 1000).toFixed(2);
  const accelVal = activeGlacier?.acceleration_m_per_day2 ?? 0.05;
  const retreatDist = activeGlacier?.retreat_distance_m ?? 120.0;
  const iceLoss = activeGlacier?.estimated_ice_loss_rate_gt_yr ?? 18.5;

  return (
    <div className="w-full h-[calc(100vh-102px)] p-4 flex flex-col gap-4 overflow-y-auto font-sans text-xs">
      {/* Top Header */}
      <div className="glass-panel p-4 rounded-xl border border-cyan-900/40 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-white">
              Agent C — Glacier & Cryosphere Hazard Early-Warning Agent
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 font-bold">
              Downstream Hazard Engine
            </span>
          </div>
          <p className="text-slate-300 text-xs mt-1 font-sans">
            Kinematic velocity & acceleration monitoring, scenario-based projections, and downstream risk evaluation.
          </p>
        </div>

        {/* Glacier Selector Tabs */}
        <div className="flex items-center gap-2">
          {effectiveGlaciers?.map((g: any) => (
            <button
              key={g.glacier_id}
              onClick={() => setSelectedGlacierId(g.glacier_id)}
              className={`px-3.5 py-1.5 rounded-lg border transition-all font-sans font-medium text-sm ${
                (activeGlacier?.glacier_id === g.glacier_id)
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-300 font-semibold shadow-md shadow-cyan-500/10'
                  : 'bg-polar-900 border-slate-800 text-slate-400 hover:text-white'
              }`}
            >
              {g.name?.split(' - ')[0] || g.name || g.glacier_id}
            </button>
          ))}
        </div>
      </div>

      {activeGlacier && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {/* Col 1: Kinematic Telemetry & Critical Status */}
          <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col gap-3.5">
            <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
              <h3 className="font-bold text-cyan-300 text-base">{activeGlacier.name}</h3>
              <span className={`px-2.5 py-0.5 rounded text-xs font-mono font-bold ${
                isCritical 
                  ? 'bg-red-950 text-red-300 border border-red-700 animate-pulse' 
                  : 'bg-emerald-950 text-emerald-300 border border-emerald-700'
              }`}>
                {accelStatus}
              </span>
            </div>

            {/* Metric Cards Grid */}
            <div className="grid grid-cols-2 gap-2.5">
              <div className="p-3 rounded-lg bg-polar-900 border border-slate-800">
                <span className="text-slate-400 text-xs font-sans block">Flow Velocity:</span>
                <span className="text-lg font-bold text-white font-mono">{velMPerDay} m/day</span>
                <span className="text-xs text-cyan-400 font-mono block mt-0.5">({velKmYr} km/yr)</span>
              </div>

              <div className="p-3 rounded-lg bg-polar-900 border border-slate-800">
                <span className="text-slate-400 text-xs font-sans block">Acceleration:</span>
                <span className={`text-lg font-bold font-mono ${accelVal > 0.2 ? 'text-red-400' : 'text-slate-200'}`}>
                  +{accelVal} m/day²
                </span>
                <span className="text-xs text-slate-400 font-sans block mt-0.5">Differential InSAR</span>
              </div>

              <div className="p-3 rounded-lg bg-polar-900 border border-slate-800">
                <span className="text-slate-400 text-xs font-sans block">Front Retreat:</span>
                <span className="text-lg font-bold text-amber-300 font-mono">{retreatDist} m</span>
                <span className="text-xs text-slate-400 font-sans block mt-0.5">Detached calving margin</span>
              </div>

              <div className="p-3 rounded-lg bg-polar-900 border border-slate-800">
                <span className="text-slate-400 text-xs font-sans block">Ice Loss Rate:</span>
                <span className="text-lg font-bold text-cyan-300 font-mono">{iceLoss} Gt/yr</span>
                <span className="text-xs text-slate-400 font-sans block mt-0.5">Mass balance deficit</span>
              </div>
            </div>

            {/* Scientific Principle Reminder */}
            <div className="p-3 rounded-lg bg-polar-950 border border-cyan-950 text-xs text-slate-300 space-y-1 font-sans">
              <span className="font-semibold text-cyan-300 flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-cyan-400" /> Scientific Principle:
              </span>
              <p className="text-slate-400 leading-relaxed">
                DeLTa rejects false-precision claims (e.g. "glacier collapses on date X"). 
                Kinematics are projected through multi-scenario uncertainty bounds with clear confidence scores.
              </p>
            </div>

            {/* Recommended Alert (if triggered) */}
            {activeGlacier.recommended_alert && (
              <div className="p-3.5 rounded-lg bg-red-950/50 border border-red-500/60 text-red-200 space-y-2 mt-auto font-sans">
                <div className="flex items-center gap-2 font-bold text-red-400 text-sm">
                  <AlertTriangle className="w-4 h-4" /> Recommended Early Warning
                </div>
                <p className="text-sm text-slate-100 leading-relaxed">{activeGlacier.recommended_alert.what}</p>
                <div className="text-xs text-amber-300 pt-1.5 border-t border-red-900/60 font-medium">
                  <span className="font-bold">Mitigation Action:</span> {activeGlacier.recommended_alert.recommended_action}
                </div>
              </div>
            )}
          </div>

          {/* Col 2 & 3: Scenario Projections & Downstream Hazard Matrix */}
          <div className="lg:col-span-2 flex flex-col gap-4">
            {/* 3-Scenario Projection Matrix */}
            <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col gap-3 font-sans">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 className="font-bold text-cyan-300 flex items-center gap-2 text-base">
                  <TrendingUp className="w-4 h-4" /> Scenario-Based Glacier Projections
                </h3>
                <span className="text-xs text-slate-400 font-sans">Calibrated Multi-Model Bounds</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {(activeGlacier.scenarios || []).map((sc: any, idx: number) => {
                  const scName = String(sc?.scenario_name || `Scenario ${idx + 1}`);
                  const isExtreme = scName.includes('High-Change');
                  const isAccelerated = scName.includes('Accelerated');
                  const annualRange = Array.isArray(sc?.annual_ice_loss_range_gt) ? sc.annual_ice_loss_range_gt : [12, 22];
                  const retreatRange = Array.isArray(sc?.retreat_velocity_range_m_yr) ? sc.retreat_velocity_range_m_yr : [800, 1100];
                  const destabilizeRange = Array.isArray(sc?.estimated_shelf_destabilization_window_years) ? sc.estimated_shelf_destabilization_window_years : [20, 40];
                  const conf = typeof sc?.confidence === 'number' ? sc.confidence : 0.85;

                  return (
                    <div 
                      key={idx}
                      className={`p-3 rounded-lg border flex flex-col gap-2 ${
                        isExtreme 
                          ? 'bg-red-950/30 border-red-500/40' 
                          : (isAccelerated ? 'bg-amber-950/30 border-amber-500/40' : 'bg-polar-900 border-slate-800')
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className={`font-semibold text-sm ${
                          isExtreme ? 'text-red-400' : (isAccelerated ? 'text-amber-300' : 'text-emerald-400')
                        }`}>
                          {scName.split(' (')[0]}
                        </span>
                        <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-polar-950 text-slate-300 font-bold">
                          {(conf * 100).toFixed(0)}% Conf.
                        </span>
                      </div>

                      <p className="text-xs text-slate-300 min-h-[36px] leading-relaxed">{sc?.description || 'Calibrated projection model'}</p>

                      <div className="pt-2 border-t border-slate-800/80 space-y-1 text-xs">
                        <div className="flex justify-between">
                          <span className="text-slate-400 text-xs">Annual Ice Loss:</span>
                          <span className="text-white font-mono font-semibold">{annualRange[0]}-{annualRange[1]} Gt</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400 text-xs">Retreat Velocity:</span>
                          <span className="text-white font-mono font-semibold">{retreatRange[0]}-{retreatRange[1]} m/yr</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-400 text-xs">Destabilization Window:</span>
                          <span className="text-cyan-300 font-mono font-semibold">{destabilizeRange[0]}-{destabilizeRange[1]} yrs</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Downstream Hazard Assessment Matrix */}
            <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col gap-3 font-sans">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800">
                <h3 className="font-bold text-cyan-300 flex items-center gap-2 text-base">
                  <Waves className="w-4 h-4" /> Downstream Hazard Assessment Matrix
                </h3>
                <span className="text-xs text-slate-400 font-sans">Plausible Downstream Consequences</span>
              </div>

              <div className="space-y-2.5">
                {(activeGlacier.downstream_hazards || []).map((hz: any, i: number) => {
                  const isCriticalHz = hz?.severity === 'CRITICAL';
                  const isHighHz = hz?.severity === 'HIGH';

                  return (
                    <div 
                      key={i}
                      className={`p-3.5 rounded-lg border flex flex-col gap-2 ${
                        isCriticalHz 
                          ? 'bg-red-950/40 border-red-500/50' 
                          : (isHighHz ? 'bg-amber-950/30 border-amber-500/40' : 'bg-polar-900 border-slate-800')
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-white text-sm flex items-center gap-2 font-sans">
                          <AlertTriangle className={`w-4 h-4 ${isCriticalHz ? 'text-red-400' : 'text-amber-400'}`} />
                          {hz?.hazard_type || 'Glacier Hazard'}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-mono font-bold ${
                            isCriticalHz ? 'bg-red-900 text-white' : 'bg-amber-900 text-amber-200'
                          }`}>
                            {hz?.severity || 'MEDIUM'}
                          </span>
                          <span className="px-2 py-0.5 rounded bg-polar-950 text-cyan-300 font-mono text-xs">
                            {hz?.probability || 'MEDIUM'}
                          </span>
                        </div>
                      </div>

                      <p className="text-sm text-slate-200 leading-relaxed font-sans">{hz?.downstream_impact_summary || 'Monitoring downstream ice discharge.'}</p>

                      <div className="mt-1 pt-2 border-t border-slate-800/80 flex items-center justify-between text-xs font-sans">
                        <span className="text-cyan-300 font-medium">
                          Action: {hz?.recommended_action || 'Maintain radar surveillance'}
                        </span>
                        <span className="text-slate-400 font-mono">{hz?.time_horizon || 'Immediate'}</span>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
