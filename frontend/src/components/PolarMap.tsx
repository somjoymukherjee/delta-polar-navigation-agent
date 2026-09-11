import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import { 
  Layers, AlertTriangle, ShieldCheck, Eye, Compass, Info,
  Fuel, Clock, ArrowRight, CheckCircle2, ChevronRight, Zap 
} from 'lucide-react';
import type { VoyagePlan, RouteCandidate } from '../services/api';
import { api } from '../services/api';

interface PolarMapProps {
  voyagePlan: VoyagePlan | null;
  features: any;
  riskGrid: any[];
  onSelectRoute?: (routeId: string) => void;
  focusedCoordinates?: [number, number] | null;
  onRefresh?: () => void;
}

export const PolarMap: React.FC<PolarMapProps> = ({
  voyagePlan,
  features,
  riskGrid,
  onSelectRoute,
  focusedCoordinates,
  onRefresh
}) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const layersRef = useRef<{ [key: string]: L.LayerGroup }>({});

  const [selectedRouteId, setSelectedRouteId] = useState<string>('ROUTE_BALANCED');
  const [showSeaIce, setShowSeaIce] = useState(true);
  const [showIcebergs, setShowIcebergs] = useState(true);
  const [showHazards, setShowHazards] = useState(true);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showAspa, setShowAspa] = useState(true);
  const [actionFeedback, setActionFeedback] = useState<string | null>(null);
  const [isSubmittingRoute, setIsSubmittingRoute] = useState(false);

  const handleRouteAction = async (actionType: 'ACCEPT_ROUTE' | 'REJECT_ROUTE' | 'MANUAL_OVERRIDE', route: RouteCandidate) => {
    if (isSubmittingRoute) return;
    setIsSubmittingRoute(true);
    let rationale = '';
    if (actionType === 'ACCEPT_ROUTE') {
      rationale = `Master of vessel approved ${route.name} (Peak Risk: ${route.peak_risk_score}/100, Dist: ${route.total_distance_nm} NM) as active navigation track.`;
    } else if (actionType === 'REJECT_ROUTE') {
      rationale = `Duty Officer rejected ${route.name} due to operational ice hazard assessment.`;
    } else {
      rationale = `Master executed manual navigation override to adopt ${route.name}.`;
    }

    try {
      await api.logAuditAction(
        actionType,
        route.route_id,
        rationale,
        {
          route_id: route.route_id,
          name: route.name,
          peak_risk: route.peak_risk_score,
          total_distance_nm: route.total_distance_nm,
          profile: route.profile
        }
      );
      setActionFeedback(`Signed & Logged: ${actionType} on ${route.name}`);
      setTimeout(() => setActionFeedback(null), 4000);
      if (onRefresh) onRefresh();
    } catch (err) {
      console.error("Failed to log route action:", err);
    } finally {
      setIsSubmittingRoute(false);
    }
  };

  // Initialize Map
  useEffect(() => {
    if (!mapContainerRef.current || mapRef.current) return;

    // Center over Weddell Sea & Antarctic Peninsula (-67.5 S, -54.0 W)
    const map = L.map(mapContainerRef.current, {
      center: [-67.5, -54.0],
      zoom: 5,
      minZoom: 3,
      maxZoom: 9,
      zoomControl: false,
    });

    L.control.zoom({ position: 'bottomright' }).addTo(map);

    // Resilient polar basemap (styled via index.css dark polar filter)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; DeLTa Polar Cartography / OpenStreetMap',
      subdomains: 'abc',
      maxZoom: 18
    }).addTo(map);

    layersRef.current = {
      routes: L.layerGroup().addTo(map),
      seaIce: L.layerGroup().addTo(map),
      icebergs: L.layerGroup().addTo(map),
      hazards: L.layerGroup().addTo(map),
      heatmap: L.layerGroup().addTo(map),
      aspa: L.layerGroup().addTo(map),
      vessel: L.layerGroup().addTo(map),
    };

    mapRef.current = map;

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // Update focused coordinates if requested
  useEffect(() => {
    if (mapRef.current && focusedCoordinates) {
      mapRef.current.flyTo(focusedCoordinates, 7, { duration: 1.5 });
    }
  }, [focusedCoordinates]);

  // Render Features & Layers
  useEffect(() => {
    if (!mapRef.current || !layersRef.current.routes) return;

    const layers = layersRef.current;

    // 1. Clear existing layers
    Object.values(layers).forEach(lg => lg.clearLayers());

    // 2. Render ASPA Protected Zones
    if (showAspa) {
      const aspa152 = L.rectangle([[-63.5, -62.5], [-63.1, -61.8]], {
        color: '#f43f5e',
        weight: 1.5,
        fillColor: '#f43f5e',
        fillOpacity: 0.15,
        dashArray: '4, 4'
      }).bindPopup(`
        <div class="text-xs font-sans p-1">
          <p class="font-bold text-rose-400">ASPA 152 - Western Bransfield</p>
          <p class="text-slate-300">Antarctic Specially Protected Area</p>
          <p class="text-amber-400 mt-1">Penalty: Strict Navigation Exclusion</p>
        </div>
      `);
      layers.aspa.addLayer(aspa152);
    }

    // 3. Render Sea Ice Concentration Polygons
    if (showSeaIce && features?.sea_ice) {
      features.sea_ice.forEach((ice: any) => {
        const bounds = ice.bounds;
        const conc = ice.concentration_pct;
        const color = conc > 70 ? '#38bdf8' : (conc > 45 ? '#0284c7' : '#0369a1');
        const opacity = conc > 70 ? 0.35 : 0.22;

        const rect = L.rectangle([[bounds.min_lat, bounds.min_lon], [bounds.max_lat, bounds.max_lon]], {
          color: color,
          weight: 1,
          fillColor: color,
          fillOpacity: opacity
        }).bindPopup(`
          <div class="text-xs font-sans p-1">
            <p class="font-bold text-cyan-300 font-mono">${ice.grid_id}</p>
            <p class="text-slate-200">Concentration: <span class="font-bold text-white font-mono">${conc}%</span></p>
            <p class="text-slate-300">Stage: ${ice.stage}</p>
            <p class="text-slate-300">Est. Thickness: <span class="font-mono">${ice.thickness_cm} cm</span></p>
            <p class="text-slate-400 text-[10px] mt-1 font-mono">${ice.sensor_type}</p>
          </div>
        `);
        layers.seaIce.addLayer(rect);
      });
    }

    // 4. Render Risk Heatmap Grid
    if (showHeatmap && riskGrid?.length) {
      riskGrid.forEach((cell: any) => {
        const b = cell?.bounds;
        if (!b || typeof b.min_lat !== 'number') return;
        const score = cell?.risk?.overall_score ?? cell?.total_risk_score ?? 0;
        let fillColor = '#10b981'; // safe
        if (score > 80) fillColor = '#ef4444'; // extreme
        else if (score > 60) fillColor = '#f97316'; // high
        else if (score > 40) fillColor = '#eab308'; // moderate
        else if (score > 20) fillColor = '#06b6d4'; // low

        const poly = L.rectangle([[b.min_lat, b.min_lon], [b.max_lat, b.max_lon]], {
          color: fillColor,
          weight: 0.5,
          fillColor: fillColor,
          fillOpacity: 0.18
        }).bindPopup(`
          <div class="text-xs font-sans p-1">
            <p class="font-semibold text-slate-100">Risk Grid: <span class="font-mono">${cell.cell_id || 'CELL'}</span></p>
            <p class="text-sm font-bold font-mono" style="color: ${fillColor}">Risk Score: ${score}/100</p>
            <p class="text-slate-300 mt-1">Driver: ${cell?.risk?.primary_driver || 'Environmental'}</p>
          </div>
        `);
        layers.heatmap.addLayer(poly);
      });
    }

    // 5. Render Glacier Hazards & Calving Fronts
    if (showHazards && features?.glaciers) {
      features.glaciers.forEach((g: any) => {
        const lat = g.front_position?.lat ?? g.front_position?.[0];
        const lon = g.front_position?.lon ?? g.front_position?.[1];
        if (lat === undefined || lon === undefined) return;

        // Front line
        const frontLine = L.polyline([
          [lat - 0.25, lon - 0.4],
          [lat, lon],
          [lat + 0.25, lon + 0.35]
        ], {
          color: g.calving_activity?.includes('CALVING') ? '#ef4444' : '#f59e0b',
          weight: 4,
          dashArray: '6, 6'
        });

        // Danger buffer circle
        const buffer = L.circle([lat, lon], {
          radius: 35000, // 35 km buffer
          color: '#ef4444',
          weight: 1,
          fillColor: '#ef4444',
          fillOpacity: 0.12
        }).bindPopup(`
          <div class="text-xs font-sans p-1">
            <p class="font-bold text-red-400">${g.name}</p>
            <p class="text-slate-200">Velocity: <span class="font-bold text-white font-mono">${g.velocity_m_per_day} m/day</span></p>
            <p class="text-slate-200">Acceleration: <span class="font-bold text-red-300 font-mono">+${g.acceleration_m_per_day2} m/day²</span></p>
            <p class="text-slate-300">Retreat: <span class="font-mono">${g.retreat_distance_m} m</span></p>
            <p class="text-amber-400 mt-1 font-semibold">Activity: ${g.calving_activity}</p>
          </div>
        `);

        layers.hazards.addLayer(frontLine);
        layers.hazards.addLayer(buffer);
      });
    }

    // 6. Render Icebergs
    if (showIcebergs && features?.icebergs) {
      features.icebergs.forEach((berg: any) => {
        const pos = berg.current_position || berg.position;
        if (!pos || pos.lat === undefined || pos.lon === undefined) return;
        const iconHtml = `
          <div class="relative flex items-center justify-center">
            <div class="w-3.5 h-3.5 rotate-45 ${berg.id.includes('CALVED') ? 'bg-red-500 border-red-300 animate-bounce' : 'bg-cyan-400 border-cyan-200'} border shadow-md flex items-center justify-center">
            </div>
            ${berg.id.includes('CALVED') ? '<span class="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-ping"></span>' : ''}
          </div>
        `;

        const icon = L.divIcon({
          html: iconHtml,
          className: 'custom-berg-icon',
          iconSize: [16, 16],
          iconAnchor: [8, 8]
        });

        const marker = L.marker([pos.lat, pos.lon], { icon }).bindPopup(`
          <div class="text-xs font-sans p-1">
            <p class="font-bold text-cyan-300 font-mono">${berg.id}</p>
            <p class="text-slate-200">Dimensions: <span class="font-mono">${berg.length_m}m x ${berg.width_m}m</span></p>
            <p class="text-slate-300">Drift: <span class="font-mono">${berg.drift_speed_knots} kt @ ${berg.drift_direction_deg}°</span></p>
            <p class="text-slate-300">Confidence: <span class="font-mono">${(berg.confidence * 100).toFixed(0)}%</span></p>
            <p class="text-[10px] text-slate-400 mt-1">Sensor: ${berg.detected_sensor}</p>
          </div>
        `);

        // Drift vector line
        const endLat = pos.lat + 0.15 * Math.cos((berg.drift_direction_deg * Math.PI) / 180);
        const endLon = pos.lon + 0.35 * Math.sin((berg.drift_direction_deg * Math.PI) / 180);
        const driftLine = L.polyline([[pos.lat, pos.lon], [endLat, endLon]], {
          color: '#38bdf8',
          weight: 1.5,
          dashArray: '2, 3',
          opacity: 0.7
        });

        layers.icebergs.addLayer(marker);
        layers.icebergs.addLayer(driftLine);
      });
    }

    // 7. Render Routes (Alpha, Bravo, Charlie)
    if (voyagePlan?.candidates) {
      voyagePlan.candidates.forEach((route: RouteCandidate) => {
        const latLngs = route.waypoints.map(wp => [wp.lat, wp.lon] as [number, number]);
        const isRec = route.recommended;
        
        let color = '#38bdf8'; // Blue for Charlie
        if (route.profile === 'BALANCED') color = '#00f0ff'; // Cyan for Alpha
        else if (route.profile === 'TIME_FIRST') color = isRec ? '#eab308' : '#ef4444'; // Red for Bravo if unsafe

        const isSelected = selectedRouteId === route.route_id;

        const line = L.polyline(latLngs, {
          color: color,
          weight: isSelected ? 5 : 3,
          opacity: isSelected ? 0.95 : 0.65,
          dashArray: route.profile === 'SAFETY_FIRST' ? '8, 6' : undefined
        });

        line.on('click', () => {
          setSelectedRouteId(route.route_id);
          if (onSelectRoute) onSelectRoute(route.route_id);
        });

        layers.routes.addLayer(line);

        // Render Waypoint Markers
        route.waypoints.forEach((wp, idx) => {
          const wpMarker = L.circleMarker([wp.lat, wp.lon], {
            radius: idx === 0 || idx === route.waypoints.length - 1 ? 6 : 4,
            color: color,
            fillColor: '#0a1120',
            fillOpacity: 1,
            weight: 2
          }).bindPopup(`
            <div class="text-xs font-sans p-1">
              <p class="font-bold text-white">${route.name} - WP${idx + 1}</p>
              <p class="text-slate-300">Leg Dist: <span class="font-mono">${wp.leg_distance_km} km</span></p>
              <p class="text-slate-300">Cumul: <span class="font-mono">${wp.cumulative_distance_km} km</span></p>
              <p class="font-bold font-mono ${wp.risk_score > 60 ? 'text-red-400' : 'text-emerald-400'}">
                Risk: ${wp.risk_score}/100
              </p>
              <p class="text-slate-300">Est. Speed: <span class="font-mono">${wp.estimated_speed_knots} kt</span></p>
              ${wp.note ? `<p class="text-[10px] text-cyan-300 mt-1">${wp.note}</p>` : ''}
            </div>
          `);
          layers.routes.addLayer(wpMarker);
        });
      });
    }

    // 8. Render Vessel Position Marker
    if (voyagePlan?.origin) {
      const vLat = voyagePlan.origin[0];
      const vLon = voyagePlan.origin[1];

      const vesselHtml = `
        <div class="relative flex items-center justify-center">
          <div class="w-6 h-6 rounded-full bg-cyan-500/20 border-2 border-cyan-400 flex items-center justify-center animate-pulse">
            <div class="w-2.5 h-2.5 bg-cyan-300 rounded-full"></div>
          </div>
          <span class="absolute -top-4 whitespace-nowrap text-[10px] font-sans font-semibold bg-polar-900/90 text-cyan-300 px-1.5 py-0.5 rounded border border-cyan-500/40">
            R/V Sir David Attenborough
          </span>
        </div>
      `;

      const vesselIcon = L.divIcon({
        html: vesselHtml,
        className: 'custom-vessel-icon',
        iconSize: [24, 24],
        iconAnchor: [12, 12]
      });

      const vMarker = L.marker([vLat, vLon], { icon: vesselIcon }).bindPopup(`
        <div class="text-xs font-sans p-1">
          <p class="font-bold text-cyan-300">R/V Sir David Attenborough</p>
          <p class="text-slate-200">Polar Class: <span class="text-emerald-400 font-mono font-bold">PC5</span></p>
          <p class="text-slate-200 font-mono">Speed: 11.2 kt | Heading: 135°</p>
          <p class="text-slate-300">Status: Navigating Weddell Approach</p>
        </div>
      `);
      layers.vessel.addLayer(vMarker);
    }

    // 9. Destination Marker
    if (voyagePlan?.destination) {
      const dLat = voyagePlan.destination[0];
      const dLon = voyagePlan.destination[1];

      const destIcon = L.divIcon({
        html: `
          <div class="flex items-center justify-center">
            <div class="w-4 h-4 rounded-full bg-emerald-500 border border-white shadow-lg shadow-emerald-500/50 flex items-center justify-center">
              <span class="w-1.5 h-1.5 bg-white rounded-full"></span>
            </div>
          </div>
        `,
        className: 'custom-dest-icon',
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      const dMarker = L.marker([dLat, dLon], { icon: destIcon }).bindPopup(`
        <div class="text-xs font-sans p-1">
          <p class="font-bold text-emerald-400">Destination: Halley VI Station</p>
          <p class="text-slate-300">Brunt Ice Shelf, Weddell Sea</p>
          <p class="text-slate-400 text-[10px] font-mono">75.58°S, 26.50°W</p>
        </div>
      `);
      layers.vessel.addLayer(dMarker);
    }

  }, [voyagePlan, features, riskGrid, selectedRouteId, showSeaIce, showIcebergs, showHazards, showHeatmap, showAspa]);

  const activeRoute = voyagePlan?.candidates?.find(r => r.route_id === selectedRouteId) || voyagePlan?.recommended_route;

  return (
    <div className="relative w-full h-[calc(100vh-102px)] flex overflow-hidden">
      {/* Map Canvas */}
      <div ref={mapContainerRef} className="flex-1 h-full z-0" />

      {/* Layer Toggles Floating HUD */}
      <div className="absolute top-4 left-4 z-10 glass-panel p-3.5 rounded-lg flex flex-col gap-2.5 max-w-[220px] text-sm font-sans">
        <div className="flex items-center justify-between pb-1.5 border-b border-slate-800">
          <span className="font-semibold text-cyan-300 flex items-center gap-1.5 text-sm">
            <Layers className="w-4 h-4" /> Map Layers
          </span>
        </div>
        <label className="flex items-center justify-between cursor-pointer text-slate-300 hover:text-white font-medium text-sm">
          <span>Sea-Ice Radar</span>
          <input type="checkbox" checked={showSeaIce} onChange={e => setShowSeaIce(e.target.checked)} className="accent-cyan-400" />
        </label>
        <label className="flex items-center justify-between cursor-pointer text-slate-300 hover:text-white font-medium text-sm">
          <span>Iceberg Targets</span>
          <input type="checkbox" checked={showIcebergs} onChange={e => setShowIcebergs(e.target.checked)} className="accent-cyan-400" />
        </label>
        <label className="flex items-center justify-between cursor-pointer text-slate-300 hover:text-white font-medium text-sm">
          <span>Glacier Fronts</span>
          <input type="checkbox" checked={showHazards} onChange={e => setShowHazards(e.target.checked)} className="accent-cyan-400" />
        </label>
        <label className="flex items-center justify-between cursor-pointer text-slate-300 hover:text-white font-medium text-sm">
          <span>Risk Heatmap</span>
          <input type="checkbox" checked={showHeatmap} onChange={e => setShowHeatmap(e.target.checked)} className="accent-cyan-400" />
        </label>
        <label className="flex items-center justify-between cursor-pointer text-slate-300 hover:text-white font-medium text-sm">
          <span>ASPA Sanctuary</span>
          <input type="checkbox" checked={showAspa} onChange={e => setShowAspa(e.target.checked)} className="accent-cyan-400" />
        </label>
      </div>

      {/* Dynamic Route Re-routing Alert Banner (if triggered) */}
      {voyagePlan?.reroute_evaluation?.reassessment_triggered && (
        <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10 glass-panel border-red-500/70 p-4 rounded-xl shadow-2xl shadow-red-500/20 max-w-xl animate-pulse">
          <div className="flex items-start gap-3">
            <div className="p-2 rounded-lg bg-red-500/20 text-red-400 border border-red-500/40 shrink-0">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div className="text-sm font-sans flex-1">
              <div className="flex items-center justify-between gap-2">
                <span className="font-bold text-red-300 uppercase tracking-wider text-base flex items-center gap-1.5 font-sans">
                  <Zap className="w-4 h-4 text-red-400" /> Dynamic Rerouting Triggered
                </span>
                <span className="text-xs font-mono px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-800 font-bold shrink-0">
                  CRITICAL HAZARD
                </span>
              </div>
              <p className="text-slate-200 mt-1.5 font-sans text-sm leading-relaxed">
                {voyagePlan.reroute_evaluation.trigger_reason}
              </p>
              <div className="mt-2.5 pt-2 border-t border-slate-800 flex items-center justify-between gap-2 text-sm">
                <span className="text-emerald-400 font-semibold font-sans">
                  Recommended: {voyagePlan.recommended_route.name}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-cyan-300 font-mono font-semibold text-xs">
                    Risk: -{voyagePlan.reroute_evaluation.risk_delta} pts
                  </span>
                  <button
                    onClick={() => handleRouteAction('ACCEPT_ROUTE', voyagePlan.recommended_route)}
                    disabled={isSubmittingRoute}
                    className="px-3 py-1 rounded bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 disabled:cursor-not-allowed text-polar-950 font-bold font-sans text-xs flex items-center gap-1 shadow-md"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" /> Authorize Reroute
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Route Comparison Side Panel */}
      <div className="w-[410px] glass-panel border-l border-cyan-950 p-4 flex flex-col gap-3.5 overflow-y-auto z-10 font-sans">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <h2 className="text-base font-bold text-cyan-300 flex items-center gap-2 font-sans">
            <Compass className="w-4 h-4" /> Polar Route Engine
          </h2>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold">
            A* Polar Mesh
          </span>
        </div>

        {/* Route Candidates List */}
        <div className="flex flex-col gap-2.5">
          {voyagePlan?.candidates?.map((r: RouteCandidate) => {
            const isSelected = selectedRouteId === r.route_id;
            const isRec = r.recommended;
            const isUnsafe = r.peak_risk_score > 60;

            return (
              <div
                key={r.route_id}
                onClick={() => setSelectedRouteId(r.route_id)}
                className={`p-3.5 rounded-lg border font-sans cursor-pointer transition-all ${
                  isSelected
                    ? 'border-cyan-400 bg-polar-800/90 shadow-lg shadow-cyan-500/10'
                    : 'border-slate-800 bg-polar-900/60 hover:border-slate-700 hover:bg-polar-850'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-base font-semibold ${isRec ? 'text-cyan-300' : (isUnsafe ? 'text-red-400' : 'text-slate-200')}`}>
                    {r.name}
                  </span>
                  {isRec && (
                    <span className="text-xs px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 flex items-center gap-1 font-bold font-sans">
                      <CheckCircle2 className="w-3.5 h-3.5" /> BEST
                    </span>
                  )}
                  {isUnsafe && !isRec && (
                    <span className="text-xs px-2 py-0.5 rounded bg-red-950 text-red-300 border border-red-700 font-bold font-sans">
                      DANGER
                    </span>
                  )}
                </div>

                <div className="grid grid-cols-3 gap-2 mt-2.5 pt-2 border-t border-slate-800/70 text-slate-300 text-xs">
                  <div>
                    <span className="text-xs text-slate-400 block font-sans">Distance:</span>
                    <span className="font-semibold text-white font-mono text-sm">{r.total_distance_nm} NM</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-sans">Duration:</span>
                    <span className="font-semibold text-white font-mono text-sm">{r.estimated_duration_hours}h</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-sans">Peak Risk:</span>
                    <span className={`font-bold font-mono text-sm ${r.peak_risk_score > 60 ? 'text-red-400' : (r.peak_risk_score > 35 ? 'text-amber-400' : 'text-emerald-400')}`}>
                      {r.peak_risk_score}/100
                    </span>
                  </div>
                </div>

                <div className="mt-2 text-xs text-slate-300 border-t border-slate-850 pt-2 font-sans leading-relaxed">
                  <p>{r.trade_offs}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Route Deep Breakdown */}
        {activeRoute && (
          <div className="p-3.5 rounded-xl bg-polar-950 border border-slate-800 text-sm font-sans flex flex-col gap-2.5 mt-auto">
            <div className="flex items-center justify-between pb-1.5 border-b border-slate-800">
              <span className="text-slate-300 font-semibold uppercase tracking-wider text-xs font-sans">
                Active Selection Metrics
              </span>
              <span className="text-xs text-cyan-300 font-mono font-bold">
                {activeRoute.total_distance_km} km
              </span>
            </div>

            <div className="grid grid-cols-2 gap-2 text-slate-300 text-sm">
              <div className="flex items-center gap-1.5">
                <Fuel className="w-4 h-4 text-cyan-400" />
                <span>Fuel: <strong className="text-white font-mono text-sm">{activeRoute.fuel_estimate_tons} tons</strong></span>
              </div>
              <div className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>Time: <strong className="text-white font-mono text-sm">{activeRoute.estimated_duration_hours} hrs</strong></span>
              </div>
            </div>

            {activeRoute.major_hazards?.length > 0 && (
              <div className="pt-2 border-t border-slate-800">
                <span className="text-xs text-slate-400 block uppercase mb-1 font-semibold font-sans">Identified Hazards:</span>
                <ul className="list-disc pl-4 text-xs text-amber-300/95 space-y-1 font-sans">
                  {activeRoute.major_hazards.map((h, i) => (
                    <li key={i}>{h}</li>
                  ))}
                </ul>
              </div>
            )}

            {activeRoute.recommended && (
              <div className="p-2.5 rounded bg-cyan-950/60 border border-cyan-500/30 text-xs text-cyan-200 font-sans leading-relaxed">
                <span className="font-bold text-white">AI Rationale:</span> This route delivers the optimal Pareto efficiency between polar class ice safety and voyage endurance.
              </div>
            )}

            {/* Operator Actions for Active Selection (Human-in-the-Loop Traceability) */}
            <div className="pt-2.5 border-t border-slate-800 flex flex-col gap-2">
              <span className="text-[11px] uppercase tracking-wider text-slate-400 font-bold font-sans">
                Operator Action (Human-in-the-Loop):
              </span>
              <div className="flex items-center gap-1.5 flex-wrap">
                <button
                  onClick={() => handleRouteAction('ACCEPT_ROUTE', activeRoute)}
                  disabled={isSubmittingRoute}
                  className="flex-1 py-1.5 px-2.5 rounded bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed text-white font-sans text-xs font-bold transition-all flex items-center justify-center gap-1 shadow-sm"
                  title="Accept route and sign audit entry"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" /> Accept Route
                </button>
                <button
                  onClick={() => handleRouteAction('REJECT_ROUTE', activeRoute)}
                  disabled={isSubmittingRoute}
                  className="py-1.5 px-2.5 rounded bg-polar-900 border border-slate-700 hover:border-red-500/60 hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed text-slate-300 font-sans text-xs font-medium transition-all"
                  title="Reject route and record reason in audit trail"
                >
                  Reject
                </button>
                <button
                  onClick={() => handleRouteAction('MANUAL_OVERRIDE', activeRoute)}
                  disabled={isSubmittingRoute}
                  className="py-1.5 px-2.5 rounded bg-amber-950/80 border border-amber-600/50 hover:bg-amber-900 disabled:opacity-50 disabled:cursor-not-allowed text-amber-200 font-sans text-xs font-medium transition-all"
                  title="Execute manual override"
                >
                  Override
                </button>
              </div>
              {actionFeedback && (
                <div className="p-2 rounded bg-emerald-950/80 border border-emerald-500/50 text-emerald-300 text-xs font-mono animate-in fade-in">
                  ✓ {actionFeedback}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
