/**
 * DeLTa Frontend API Client
 * Connects to the FastAPI backend services.
 * Features automated resilient fallback for public cloud deployment (e.g. Vercel).
 */

import {
  FALLBACK_STATUS,
  FALLBACK_VOYAGE_PLAN,
  FALLBACK_ALERTS,
  FALLBACK_GLACIERS,
  FALLBACK_SATELLITE_FEATURES,
  FALLBACK_CHAT,
  ROUTE_ALPHA,
  ROUTE_BRAVO,
  ROUTE_CHARLIE
} from './fallbackData';

const isDev = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
  (window.location.port === '5173' || window.location.port === '4173');

const customUrl = typeof window !== 'undefined' ? localStorage.getItem('DELTA_API_URL') : null;
export const hasLiveBackend = isDev || !!customUrl || !!import.meta.env.VITE_API_BASE_URL;
export const API_BASE = customUrl || import.meta.env.VITE_API_BASE_URL || (isDev ? 'http://localhost:8000/api' : '/api');

// Local demo state for standalone Vercel preview
let localStage = 0;
let localAlerts = [...FALLBACK_ALERTS];
let localChatHistory = [...FALLBACK_CHAT];
let localVoyagePlan = { ...FALLBACK_VOYAGE_PLAN };
let localStatus = { ...FALLBACK_STATUS };

async function safeFetch<T>(url: string, options?: RequestInit, fallbackValue?: T): Promise<T> {
  if (!hasLiveBackend && fallbackValue !== undefined) {
    return fallbackValue;
  }
  try {
    const res = await fetch(url, { ...options, signal: AbortSignal.timeout(4000) });
    if (!res.ok) {
      if (fallbackValue !== undefined) return fallbackValue;
      throw new Error(`HTTP ${res.status}`);
    }
    const text = await res.text();
    try {
      return JSON.parse(text);
    } catch {
      if (fallbackValue !== undefined) return fallbackValue;
      throw new Error('Invalid JSON response');
    }
  } catch (err) {
    if (fallbackValue !== undefined) return fallbackValue;
    throw err;
  }
}

export interface SystemStatus {
  system_name: string;
  mode: 'LIVE' | 'DEMO' | 'HISTORICAL_REPLAY';
  current_step: string;
  scenario_stage: number;
  scenario_name: string;
  scenario_step_name: string;
  last_cycle_timestamp: string;
  active_alerts_count: number;
  vessel_name: string;
  polar_class: string;
  coordinates: [number, number];
  timestamp: string;
}

export interface RouteWaypoint {
  lat: number;
  lon: number;
  leg_distance_km: number;
  cumulative_distance_km: number;
  risk_score: number;
  estimated_speed_knots: number;
  ice_concentration_pct: number;
  note?: string;
}

export interface RouteCandidate {
  route_id: string;
  profile: string;
  name: string;
  waypoints: RouteWaypoint[];
  total_distance_km: number;
  total_distance_nm: number;
  estimated_duration_hours: number;
  average_risk_score: number;
  peak_risk_score: number;
  fuel_estimate_tons: number;
  major_hazards: string[];
  trade_offs: string;
  recommended: boolean;
  generated_at: string;
}

export interface VoyagePlan {
  vessel_id: string;
  origin: [number, number];
  destination: [number, number];
  destination_name: string;
  recommended_route: RouteCandidate;
  candidates: RouteCandidate[];
  reroute_evaluation: {
    reassessment_triggered: boolean;
    trigger_reason: string;
    old_route_id?: string;
    recommended_route: RouteCandidate;
    alternative_routes: RouteCandidate[];
    risk_delta: number;
    explanation: string;
  };
  decision_explanation: {
    decision: string;
    primary_evidence: string[];
    risk_factors: Record<string, number>;
    confidence_pct: number;
    alternatives_considered: string[];
    trade_off: string;
    recommended_action: string;
  };
}

export interface Alert {
  alert_id: string;
  severity: 'NORMAL' | 'WATCH' | 'ADVISORY' | 'WARNING' | 'CRITICAL';
  what: string;
  where_lat: number;
  where_lon: number;
  where_location_name: string;
  when_timestamp: string;
  evidence: string;
  confidence: number;
  expected_development: string;
  recommended_action: string;
  acknowledged: boolean;
  acknowledged_by?: string;
  acknowledged_at?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  tool_calls?: Array<{ tool: string; params: any }>;
  decision_card?: any;
}

export const api = {
  getStatus: async (): Promise<SystemStatus> => {
    return safeFetch<SystemStatus>(`${API_BASE}/status`, undefined, {
      ...localStatus,
      scenario_stage: localStage,
      timestamp: new Date().toISOString()
    });
  },

  setMode: async (mode: string): Promise<any> => {
    try {
      const res = await fetch(`${API_BASE}/mode?mode=${mode}`, { method: 'POST', signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
    } catch {}
    localStatus.mode = mode as any;
    return { status: "MODE_UPDATED", mode };
  },

  getVessel: async (): Promise<any> => {
    return safeFetch(`${API_BASE}/vessel`, undefined, {
      vessel_name: "R/V Sir David Attenborough",
      polar_class: "PC5",
      coordinates: [-64.82, -63.5]
    });
  },

  getRoutes: async (): Promise<VoyagePlan> => {
    return safeFetch<VoyagePlan>(`${API_BASE}/routes`, undefined, localVoyagePlan);
  },

  getSatellitePasses: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/satellite/passes`, undefined, [
      {
        pass_id: "PASS-S1A-EW-902",
        satellite: "Sentinel-1A",
        instrument: "C-Band Synthetic Aperture Radar (SAR)",
        mode: "Extra Wide Swath (EW)",
        polarization: "HH+HV Dual-Pol",
        swath_width_km: 400,
        resolution_m: 20,
        acquisition_time: new Date(Date.now() - 3600000).toISOString(),
        coverage_region: "Antarctic Peninsula & Western Weddell Sea",
        status: "PROCESSED_CALIBRATED",
        quality_score: 0.98
      },
      {
        pass_id: "PASS-S2B-MSI-441",
        satellite: "Sentinel-2B",
        instrument: "Multi-Spectral Instrument (MSI)",
        mode: "Optical 13-Band",
        polarization: "N/A",
        swath_width_km: 290,
        resolution_m: 10,
        acquisition_time: new Date(Date.now() - 7200000).toISOString(),
        coverage_region: "Larsen C Ice Shelf Rifts",
        status: "ATMOSPHERICALLY_CORRECTED",
        quality_score: 0.94
      }
    ]);
  },

  getSatelliteFeatures: async (): Promise<any> => {
    return safeFetch<any>(`${API_BASE}/satellite/features`, undefined, FALLBACK_SATELLITE_FEATURES);
  },

  getTemporalChange: async (): Promise<any> => {
    return safeFetch<any>(`${API_BASE}/satellite/temporal-change`, undefined, FALLBACK_SATELLITE_FEATURES.temporal_change);
  },

  getGlaciers: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/hazards/glaciers`, undefined, FALLBACK_GLACIERS);
  },

  getRiskGrid: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/risk/grid`, undefined, [
      {
        cell_id: "GRID_GERLACHE",
        bounds: { min_lat: -65.5, max_lat: -64.2, min_lon: -64.0, max_lon: -62.0 },
        risk: { overall_score: 18.2, primary_driver: "Open Pack Ice", factors: { sea_ice_risk: 12.0 } }
      },
      {
        cell_id: "GRID_LARSEN_FRONT",
        bounds: { min_lat: -66.5, max_lat: -65.2, min_lon: -61.5, max_lon: -58.5 },
        risk: { overall_score: localStage === 2 ? 84.5 : (localStage === 1 ? 62.0 : 38.0), primary_driver: localStage === 2 ? "Catastrophic Calving Blockage" : "Katabatic Compression", factors: { iceberg_risk: localStage === 2 ? 88.0 : 35.0 } }
      },
      {
        cell_id: "GRID_WEDDELL_BASIN",
        bounds: { min_lat: -68.5, max_lat: -66.5, min_lon: -56.0, max_lon: -50.0 },
        risk: { overall_score: 24.5, primary_driver: "Open Swell", factors: { weather_risk: 22.0 } }
      }
    ]);
  },

  getAlerts: async (): Promise<Alert[]> => {
    return safeFetch<Alert[]>(`${API_BASE}/alerts`, undefined, localAlerts);
  },

  acknowledgeAlert: async (alertId: string, operatorId = 'DUTY_OFFICER'): Promise<Alert> => {
    try {
      const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge?operator_id=${operatorId}`, { method: 'POST' });
      if (res.ok) return await res.json();
    } catch {}
    localAlerts = localAlerts.map(a => a.alert_id === alertId ? { ...a, acknowledged: true, acknowledged_by: operatorId, acknowledged_at: new Date().toISOString() } : a);
    return localAlerts.find(a => a.alert_id === alertId)!;
  },

  getChatHistory: async (): Promise<ChatMessage[]> => {
    return safeFetch<ChatMessage[]>(`${API_BASE}/chat/history`, undefined, localChatHistory);
  },

  sendChatMessage: async (message: string): Promise<ChatMessage> => {
    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: AbortSignal.timeout(5000)
      });
      if (res.ok) return await res.json();
    } catch {}

    const reply: ChatMessage = {
      id: `ASSISTANT-${Date.now()}`,
      role: 'assistant',
      content: `[DeLTa Multi-Agent Intelligence Core] Received query: "${message}". Vessel R/V Sir David Attenborough is operating on Polar Class PC5 standards at 64.82°S, 63.50°W. Active track is Route Alpha (Balanced Track, Peak Risk 27.6/100). All SAR and Optical sensors report continuous lead navigability.`,
      timestamp: new Date().toISOString(),
      decision_card: {
        title: "Polar Route Feasibility Advisory",
        confidence: "94%",
        recommendation: "Maintain Route Alpha trackline to Halley VI."
      }
    };
    localChatHistory.push(reply);
    return reply;
  },

  stepSimulation: async (stage: number): Promise<any> => {
    try {
      const res = await fetch(`${API_BASE}/simulation/step`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stage }),
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) return await res.json();
    } catch {}

    localStage = stage;
    if (stage === 0) {
      localStatus.scenario_step_name = "T+0: Baseline Departure";
      localVoyagePlan = { ...FALLBACK_VOYAGE_PLAN };
    } else if (stage === 1) {
      localStatus.scenario_step_name = "T+6h: Storm Inflow & Pack Ice Compression";
      localAlerts.unshift({
        alert_id: `ALERT-STORM-${Date.now()}`,
        severity: "WARNING",
        what: "Severe Katabatic Pressure Drop (968 hPa, 48 kt gusts)",
        where_lat: -65.5,
        where_lon: -60.0,
        where_location_name: "Larsen C Inshore Channel",
        when_timestamp: new Date().toISOString(),
        evidence: "Rapid barometric collapse detected by Open-Meteo & shipboard barograph.",
        confidence: 0.91,
        expected_development: "Compression of first-year pack ice against fast ice edge.",
        recommended_action: "Reduce transit speed and alter heading 15° seaward.",
        acknowledged: false
      });
    } else {
      localStatus.scenario_step_name = "T+12h: Major Calving Event & Active Rerouting";
      localAlerts.unshift({
        alert_id: `ALERT-CALVING-${Date.now()}`,
        severity: "CRITICAL",
        what: "Major Glacier Calving Detachment & Inshore Track Obstruction",
        where_lat: -66.2,
        where_lon: -60.5,
        where_location_name: "Larsen C Northern Rift Section",
        when_timestamp: new Date().toISOString(),
        evidence: "Sentinel-1 EW SAR indicates 820m tabular detachment. 5 major bergs adrift directly across Route Bravo.",
        confidence: 0.97,
        expected_development: "Complete blockage of high-speed inshore passage within 3 hours.",
        recommended_action: "EXECUTE DYNAMIC REROUTE: Shift immediately to Route Alpha (Balanced Deep Corridor).",
        acknowledged: false
      });
      localVoyagePlan = {
        ...FALLBACK_VOYAGE_PLAN,
        reroute_evaluation: {
          reassessment_triggered: true,
          trigger_reason: "Direct track obstruction by 820m tabular calving event",
          old_route_id: "ROUTE_TIME_FIRST",
          recommended_route: ROUTE_ALPHA,
          alternative_routes: [ROUTE_BRAVO, ROUTE_CHARLIE],
          risk_delta: -48.2,
          explanation: "Route Bravo compromised (Peak Risk 84/100). Diverted vessel to Route Alpha (Peak Risk 27.6/100)."
        }
      };
    }
    return { stage, step_name: localStatus.scenario_step_name };
  },

  triggerCalvingEvent: async (): Promise<any> => {
    return api.stepSimulation(2);
  },

  resetSimulation: async (): Promise<any> => {
    localStage = 0;
    localAlerts = [...FALLBACK_ALERTS];
    localVoyagePlan = { ...FALLBACK_VOYAGE_PLAN };
    return api.stepSimulation(0);
  },

  getAuditLogs: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/audit`, undefined, [
      {
        log_id: "AUDIT-001",
        action_type: "EXECUTE_SIMULATION",
        target_id: "STAGE_0",
        rationale: "Operator initialized Weddell Baseline T+0 scenario [DEMO Provenance]",
        operator_id: "DUTY_OFFICER",
        timestamp: new Date().toISOString()
      }
    ]);
  },

  logAuditAction: async (actionType: string, targetId: string, rationale: string, details?: any): Promise<any> => {
    return safeFetch(`${API_BASE}/audit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_type: actionType, target_id: targetId, rationale, details })
    }, { status: "LOGGED_LOCAL" });
  },

  getAgentState: async (): Promise<any> => {
    return safeFetch(`${API_BASE}/agent/state`, undefined, { state: "NOMINAL", cycle: 1 });
  },

  getAgentActivity: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/agent/activity`, undefined, [
      {
        id: "ACT-01",
        timestamp: new Date().toISOString(),
        agent: "Navigation Agent",
        activity: "Evaluated 3 candidate tracks over A* polar cost mesh. Recommended Route Alpha.",
        level: "INFO"
      },
      {
        id: "ACT-02",
        timestamp: new Date().toISOString(),
        agent: "Hazard Sentinel",
        activity: "Fused Sentinel-1 SAR + Sentinel-2 MSI data. Track clear of catastrophic compression.",
        level: "SUCCESS"
      }
    ]);
  },

  getNormalizedObservations: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/observations/normalized`, undefined, []);
  },

  getRiskDelta: async (): Promise<any> => {
    return safeFetch<any>(`${API_BASE}/risk/delta`, undefined, {
      delta_percentage: localStage === 2 ? 42.5 : (localStage === 1 ? 14.8 : 0.0),
      trend: localStage > 0 ? "INCREASING" : "STABLE",
      confidence: 0.94
    });
  },

  getSharedState: async (): Promise<any> => {
    return safeFetch<any>(`${API_BASE}/system/shared-state`, undefined, {
      system_mode: "DEMO",
      current_step: "MONITOR",
      active_route: "Route Alpha"
    });
  },

  getAgentCycles: async (): Promise<any[]> => {
    return safeFetch<any[]>(`${API_BASE}/agent/cycles`, undefined, []);
  },
};
