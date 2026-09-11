/**
 * DeLTa Frontend API Client
 * Connects to the FastAPI backend services.
 */

const isDev = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') &&
  (window.location.port === '5173' || window.location.port === '4173');

const API_BASE = import.meta.env.VITE_API_BASE_URL || (isDev ? 'http://localhost:8000/api' : '/api');

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
    const res = await fetch(`${API_BASE}/status`);
    return res.json();
  },

  setMode: async (mode: string): Promise<any> => {
    const res = await fetch(`${API_BASE}/mode?mode=${mode}`, { method: 'POST' });
    return res.json();
  },

  getVessel: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/vessel`);
    return res.json();
  },

  getRoutes: async (): Promise<VoyagePlan> => {
    const res = await fetch(`${API_BASE}/routes`);
    return res.json();
  },

  getSatellitePasses: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/satellite/passes`);
    return res.json();
  },

  getSatelliteFeatures: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/satellite/features`);
    return res.json();
  },

  getTemporalChange: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/satellite/temporal-change`);
    return res.json();
  },

  getGlaciers: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/hazards/glaciers`);
    return res.json();
  },

  getRiskGrid: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/risk/grid`);
    return res.json();
  },

  getAlerts: async (): Promise<Alert[]> => {
    const res = await fetch(`${API_BASE}/alerts`);
    return res.json();
  },

  acknowledgeAlert: async (alertId: string, operatorId = 'DUTY_OFFICER'): Promise<Alert> => {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge?operator_id=${operatorId}`, {
      method: 'POST',
    });
    return res.json();
  },

  getChatHistory: async (): Promise<ChatMessage[]> => {
    const res = await fetch(`${API_BASE}/chat/history`);
    return res.json();
  },

  sendChatMessage: async (message: string): Promise<ChatMessage> => {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    return res.json();
  },

  stepSimulation: async (stage: number): Promise<any> => {
    const res = await fetch(`${API_BASE}/simulation/step`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ stage }),
    });
    return res.json();
  },

  triggerCalvingEvent: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/simulation/calving-event`, { method: 'POST' });
    return res.json();
  },

  resetSimulation: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/simulation/reset`, { method: 'POST' });
    return res.json();
  },

  getAuditLogs: async (): Promise<any[]> => {
    try {
      const res = await fetch(`${API_BASE}/audit`);
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch (e) {
      console.error("Error loading audit logs:", e);
      return [];
    }
  },

  logAuditAction: async (actionType: string, targetId: string, rationale: string, details?: any): Promise<any> => {
    const res = await fetch(`${API_BASE}/audit`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action_type: actionType, target_id: targetId, rationale, details }),
    });
    return res.json();
  },

  getAgentState: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/agent/state`);
    return res.json();
  },

  getAgentActivity: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/agent/activity`);
    return res.json();
  },

  getNormalizedObservations: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/observations/normalized`);
    return res.json();
  },

  getRiskDelta: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/risk/delta`);
    return res.json();
  },

  getSharedState: async (): Promise<any> => {
    const res = await fetch(`${API_BASE}/system/shared-state`);
    return res.json();
  },

  getAgentCycles: async (): Promise<any[]> => {
    const res = await fetch(`${API_BASE}/agent/cycles`);
    return res.json();
  },
};
