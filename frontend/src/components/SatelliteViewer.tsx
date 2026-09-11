import React, { useState } from 'react';
import { 
  Radio, Eye, Sparkles, Layers, Sliders, Calendar,
  ShieldCheck, AlertTriangle, ArrowLeftRight, CheckCircle2 
} from 'lucide-react';

interface SatelliteViewerProps {
  temporalChange: any;
  passes: any[];
}

export const SatelliteViewer: React.FC<SatelliteViewerProps> = ({
  temporalChange,
  passes
}) => {
  const [sliderPos, setSliderPos] = useState<number>(50);
  const [sensorType, setSensorType] = useState<'SAR' | 'OPTICAL'>('SAR');
  const [showBergs, setShowBergs] = useState<boolean>(true);
  const [showFrontRetreat, setShowFrontRetreat] = useState<boolean>(true);
  const [showDiffMask, setShowDiffMask] = useState<boolean>(true);

  const isAccelerated = temporalChange?.acceleration_detected || false;
  const iceDelta = temporalChange?.sea_ice_concentration_delta_pct || 25.5;
  const bergDelta = temporalChange?.iceberg_count_delta || 5;
  const retreatM = Math.abs(temporalChange?.front_displacement_m || 820);

  return (
    <div className="w-full h-[calc(100vh-102px)] p-4 flex flex-col gap-4 overflow-y-auto">
      {/* Top Header & Telemetry Summary */}
      <div className="flex flex-wrap items-center justify-between gap-4 glass-panel p-4 rounded-xl border border-cyan-900/40">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-cyan-400" />
            <h2 className="text-lg font-bold font-sans text-white">
              Multi-Temporal Earth Observation & SAR/Optical Fusion Engine
            </h2>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              Copernicus Sentinel-1/2
            </span>
          </div>
          <p className="text-xs font-sans text-slate-300 mt-1">
            Temporal change analysis: Baseline historical pass (T0) vs recent polar acquisition (T1)
          </p>
        </div>

        {/* Change Metrics HUD */}
        <div className="flex items-center gap-3 text-sm font-sans">
          <div className="px-3.5 py-2 rounded-lg bg-polar-900 border border-slate-800">
            <span className="text-slate-400 block text-xs">Sea-Ice Delta:</span>
            <span className={`font-mono font-bold text-base ${iceDelta > 15 ? 'text-red-400' : 'text-cyan-300'}`}>
              +{iceDelta}% surge
            </span>
          </div>
          <div className="px-3.5 py-2 rounded-lg bg-polar-900 border border-slate-800">
            <span className="text-slate-400 block text-xs">Calved Icebergs:</span>
            <span className="font-mono font-bold text-base text-amber-300">
              +{bergDelta} new targets
            </span>
          </div>
          <div className="px-3.5 py-2 rounded-lg bg-polar-900 border border-slate-800">
            <span className="text-slate-400 block text-xs">Front Retreat:</span>
            <span className={`font-mono font-bold text-base ${retreatM > 500 ? 'text-red-400' : 'text-slate-200'}`}>
              -{retreatM} meters
            </span>
          </div>
          <div className="px-3.5 py-2 rounded-lg bg-polar-900 border border-slate-800">
            <span className="text-slate-400 block text-xs">CV Confidence:</span>
            <span className="font-mono font-bold text-base text-emerald-400">
              {((temporalChange?.confidence || 0.94) * 100).toFixed(0)}%
            </span>
          </div>
        </div>
      </div>

      {/* Main Imagery Comparison Split View */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-4 min-h-[500px]">
        {/* Left 3 Cols: Interactive Split Slider Canvas */}
        <div className="lg:col-span-3 glass-panel rounded-xl overflow-hidden relative border border-slate-800 flex flex-col">
          {/* Controls Bar */}
          <div className="px-4 py-2.5 bg-polar-900/90 border-b border-slate-800 flex items-center justify-between z-10 text-sm font-sans">
            <div className="flex items-center gap-2">
              <span className="text-slate-300 font-medium text-sm">Sensor Mode:</span>
              <button
                onClick={() => setSensorType('SAR')}
                className={`px-3 py-1.5 rounded transition-all font-medium text-sm ${
                  sensorType === 'SAR' ? 'bg-cyan-500 text-polar-950 font-bold' : 'bg-polar-800 text-slate-300'
                }`}
              >
                Sentinel-1 C-SAR (Radar)
              </button>
              <button
                onClick={() => setSensorType('OPTICAL')}
                className={`px-3 py-1.5 rounded transition-all font-medium text-sm ${
                  sensorType === 'OPTICAL' ? 'bg-cyan-500 text-polar-950 font-bold' : 'bg-polar-800 text-slate-300'
                }`}
              >
                Sentinel-2 MSI (Optical NDSI)
              </button>
            </div>

            <div className="flex items-center gap-3.5">
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 hover:text-white text-sm">
                <input type="checkbox" checked={showBergs} onChange={e => setShowBergs(e.target.checked)} className="accent-cyan-400" />
                <span>Iceberg Detections</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 hover:text-white text-sm">
                <input type="checkbox" checked={showFrontRetreat} onChange={e => setShowFrontRetreat(e.target.checked)} className="accent-cyan-400" />
                <span>Calving Line</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer text-slate-300 hover:text-white text-sm">
                <input type="checkbox" checked={showDiffMask} onChange={e => setShowDiffMask(e.target.checked)} className="accent-cyan-400" />
                <span>Difference Heatmap</span>
              </label>
            </div>
          </div>

          {/* Interactive Split Canvas */}
          <div className="relative flex-1 w-full h-full min-h-[440px] bg-slate-950 select-none overflow-hidden">
            {/* Background Layer: T0 Baseline Scene */}
            <div 
              className="absolute inset-0 w-full h-full flex items-center justify-center"
              style={{
                background: sensorType === 'SAR' 
                  ? 'radial-gradient(circle at 40% 40%, #1e293b 0%, #0f172a 40%, #020617 90%)'
                  : 'radial-gradient(circle at 40% 40%, #bae6fd 0%, #38bdf8 30%, #0369a1 90%)'
              }}
            >
              {/* Synthetic Polar Continental Shelf & Fast Ice Outline */}
              <svg className="w-full h-full opacity-60 pointer-events-none" viewBox="0 0 800 600">
                {/* Baseline Shelf Boundary */}
                <path d="M 150,0 Q 280,180 320,300 T 450,600 L 0,600 L 0,0 Z" fill={sensorType === 'SAR' ? '#334155' : '#e0f2fe'} />
                {/* T0 Baseline Front (Dashed green) */}
                <path d="M 320,300 Q 380,360 450,600" stroke="#10b981" strokeWidth="4" strokeDasharray="8 6" fill="none" />
                <text x="340" y="290" fill="#10b981" fontSize="13" fontFamily="monospace" fontWeight="bold">T0 Ice Front Baseline</text>
                
                {/* Baseline Bergs (few) */}
                <rect x="420" y="240" width="22" height="15" fill="#f8fafc" stroke="#38bdf8" strokeWidth="2" />
                <rect x="490" y="320" width="18" height="12" fill="#f8fafc" stroke="#38bdf8" strokeWidth="2" />
              </svg>

              <div className="absolute bottom-4 left-4 bg-polar-950/80 px-2.5 py-1 rounded border border-slate-700 text-xs font-mono text-emerald-400">
                ◄ T0 Baseline Pass (5 Days Ago)
              </div>
            </div>

            {/* Foreground Clipped Layer: T1 Recent Scene */}
            <div 
              className="absolute inset-0 w-full h-full overflow-hidden"
              style={{ clipPath: `inset(0 0 0 ${sliderPos}%)` }}
            >
              <div 
                className="w-full h-full flex items-center justify-center"
                style={{
                  background: sensorType === 'SAR'
                    ? 'radial-gradient(circle at 40% 40%, #334155 0%, #1e293b 40%, #020617 90%)'
                    : 'radial-gradient(circle at 40% 40%, #7dd3fc 0%, #0284c7 40%, #082f49 90%)'
                }}
              >
                <svg className="w-full h-full opacity-80 pointer-events-none" viewBox="0 0 800 600">
                  {/* Calved / Retreated Shelf Outline */}
                  <path d="M 150,0 Q 280,180 260,300 T 370,600 L 0,600 L 0,0 Z" fill={sensorType === 'SAR' ? '#475569' : '#bae6fd'} />
                  
                  {/* T1 Calved Front Line (Red) */}
                  {showFrontRetreat && (
                    <>
                      <path d="M 260,300 Q 320,380 370,600" stroke="#ef4444" strokeWidth="4" fill="none" />
                      <text x="270" y="350" fill="#ef4444" fontSize="13" fontFamily="monospace" fontWeight="bold">
                        T1 Detached Front (-820m)
                      </text>
                    </>
                  )}

                  {/* Difference Mask Shading between T0 and T1 */}
                  {showDiffMask && (
                    <path d="M 320,300 Q 380,360 450,600 L 370,600 Q 320,380 260,300 Z" fill="rgba(239, 68, 68, 0.45)" stroke="#ef4444" strokeWidth="1" strokeDasharray="4 4" />
                  )}

                  {/* Detected New Tabular Icebergs */}
                  {showBergs && (
                    <>
                      <g>
                        <rect x="360" y="320" width="45" height="28" fill="#f8fafc" stroke="#ef4444" strokeWidth="2.5" />
                        <text x="360" y="310" fill="#ef4444" fontSize="11" fontFamily="monospace" fontWeight="bold">BERG-CALVED-01 (640m)</text>
                      </g>
                      <g>
                        <rect x="420" y="380" width="35" height="22" fill="#f8fafc" stroke="#ef4444" strokeWidth="2" />
                        <text x="420" y="372" fill="#ef4444" fontSize="11" fontFamily="monospace" fontWeight="bold">BERG-CALVED-02</text>
                      </g>
                      <g>
                        <rect x="390" y="440" width="38" height="25" fill="#f8fafc" stroke="#ef4444" strokeWidth="2" />
                        <text x="390" y="432" fill="#ef4444" fontSize="11" fontFamily="monospace" fontWeight="bold">BERG-CALVED-03</text>
                      </g>
                    </>
                  )}
                </svg>

                <div className="absolute bottom-4 right-4 bg-polar-950/80 px-2.5 py-1 rounded border border-slate-700 text-xs font-mono text-cyan-300">
                  T1 Recent Pass (45m Ago) ►
                </div>
              </div>
            </div>

            {/* Split Divider Handle */}
            <div 
              className="absolute top-0 bottom-0 w-1 bg-cyan-400 shadow-lg shadow-cyan-400/80 cursor-ew-resize z-20 flex items-center justify-center"
              style={{ left: `${sliderPos}%` }}
            >
              <div className="w-8 h-8 rounded-full bg-polar-900 border-2 border-cyan-400 text-cyan-300 flex items-center justify-center shadow-md">
                <ArrowLeftRight className="w-4 h-4" />
              </div>
            </div>

            {/* Slider Input overlay */}
            <input 
              type="range"
              min="5"
              max="95"
              value={sliderPos}
              onChange={(e) => setSliderPos(Number(e.target.value))}
              className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-30"
            />
          </div>

          {/* Slider Position Footer */}
          <div className="px-4 py-2 bg-polar-900/80 border-t border-slate-800 text-xs font-sans text-slate-400 flex items-center justify-between">
            <span>Drag slider horizontally to cross-fade between T0 Baseline and T1 Calving event</span>
            <span className="text-cyan-300 font-mono font-medium">Curtain: {sliderPos}%</span>
          </div>
        </div>

        {/* Right Col: AI CV Extraction & Metadata HUD */}
        <div className="glass-panel p-4 rounded-xl border border-slate-800 flex flex-col gap-3.5 text-sm font-sans">
          <div className="pb-2 border-b border-slate-800">
            <h3 className="font-bold text-cyan-300 uppercase tracking-wider flex items-center gap-2 font-sans text-base">
              <Sparkles className="w-4 h-4 text-cyan-400" /> Computer Vision Telemetry
            </h3>
          </div>

          {/* Sensor Info */}
          <div className="p-3.5 rounded-lg bg-polar-900 border border-slate-800/80 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Sensor:</span>
              <span className="text-white font-semibold">{sensorType === 'SAR' ? 'Sentinel-1 C-Band SAR' : 'Sentinel-2 MSI'}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Polarization:</span>
              <span className="text-cyan-300 font-mono">HH + HV Dual-Pol</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Ground Resolution:</span>
              <span className="text-white font-mono">10.0 meters / pixel</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Cloud Penetration:</span>
              <span className="text-emerald-400 font-mono font-bold">100% (Radar Coherent)</span>
            </div>
          </div>

          {/* Detected Cryosphere Anomalies */}
          <div className="space-y-2">
            <span className="text-slate-400 font-bold uppercase tracking-wider text-xs block font-sans">
              Detected Anomalies (T0 vs T1):
            </span>
            <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-200 space-y-1.5">
              <div className="flex items-center gap-1.5 font-bold text-red-400 font-sans text-sm">
                <AlertTriangle className="w-4 h-4" /> Ice Front Detachment
              </div>
              <p className="text-sm text-slate-200 font-sans leading-relaxed">
                {temporalChange?.summary || 'Catastrophic ice-front calving (-820m detachment) detected.'}
              </p>
            </div>
          </div>

          {/* Feature List */}
          <div className="space-y-2 mt-auto pt-2.5 border-t border-slate-800 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-400">Ice Shelf Fracture:</span>
              <span className="text-red-400 font-mono font-bold">ACTIVE CALVING</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Tabular Bergs Identified:</span>
              <span className="text-white font-mono font-bold">3 Primary Massive</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Drift Trajectory:</span>
              <span className="text-cyan-300 font-mono font-semibold">0.85 kt @ 045° (NE)</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
