/**
 * DeLTa Standalone Offline / Demo Fallback Data
 * Ensures the public Vercel deployment provides complete, rich, interactive
 * visual intelligence even when a local backend is not actively connected.
 */

import type { SystemStatus, VoyagePlan, Alert, ChatMessage, RouteCandidate } from './api';

export const FALLBACK_STATUS: SystemStatus = {
  system_name: "DeLTa Polar Intelligence Platform",
  mode: "DEMO",
  current_step: "MONITOR",
  scenario_stage: 0,
  scenario_name: "Weddell Sea Calving & Katabatic Pack Ice Convergence",
  scenario_step_name: "T+0: Baseline Departure",
  last_cycle_timestamp: new Date().toISOString(),
  active_alerts_count: 1,
  vessel_name: "R/V Sir David Attenborough",
  polar_class: "PC5",
  coordinates: [-64.82, -63.5],
  timestamp: new Date().toISOString()
};

export const ROUTE_ALPHA: RouteCandidate = {
  route_id: "ROUTE_BALANCED",
  profile: "BALANCED",
  name: "Route Alpha (Balanced - Recommended)",
  waypoints: [
    { lat: -64.82, lon: -63.5, leg_distance_km: 0, cumulative_distance_km: 0, risk_score: 18.2, estimated_speed_knots: 12.0, ice_concentration_pct: 15.0, note: "Departure Gerlache" },
    { lat: -64.5, lon: -61.0, leg_distance_km: 128.5, cumulative_distance_km: 128.5, risk_score: 22.4, estimated_speed_knots: 11.5, ice_concentration_pct: 25.0, note: "Entering Antarctic Sound" },
    { lat: -64.0, lon: -57.5, leg_distance_km: 180.2, cumulative_distance_km: 308.7, risk_score: 24.1, estimated_speed_knots: 11.0, ice_concentration_pct: 35.0, note: "North Larsen Standoff" },
    { lat: -65.2, lon: -53.0, leg_distance_km: 245.0, cumulative_distance_km: 553.7, risk_score: 27.6, estimated_speed_knots: 10.5, ice_concentration_pct: 42.0, note: "Open Drift Corridor" },
    { lat: -68.0, lon: -46.0, leg_distance_km: 410.0, cumulative_distance_km: 963.7, risk_score: 23.0, estimated_speed_knots: 12.0, ice_concentration_pct: 28.0, note: "Mid-Weddell Basin" },
    { lat: -71.5, lon: -38.0, leg_distance_km: 512.0, cumulative_distance_km: 1475.7, risk_score: 21.5, estimated_speed_knots: 12.2, ice_concentration_pct: 20.0, note: "Approaching Halley Lead" },
    { lat: -75.58, lon: -26.55, leg_distance_km: 592.5, cumulative_distance_km: 2068.2, risk_score: 19.8, estimated_speed_knots: 11.8, ice_concentration_pct: 18.0, note: "Halley VI Arrival" }
  ],
  total_distance_km: 2068.2,
  total_distance_nm: 1116.7,
  estimated_duration_hours: 97.1,
  average_risk_score: 22.4,
  peak_risk_score: 27.6,
  fuel_estimate_tons: 104.2,
  major_hazards: [
    "Localized compression in Prince Gustav Channel",
    "Tabular iceberg drift along 55°W meridian"
  ],
  trade_offs: "Distance: 1116.7 NM | Est. Time: 97.1h | Peak Risk: 27.6/100",
  recommended: true,
  generated_at: new Date().toISOString()
};

export const ROUTE_BRAVO: RouteCandidate = {
  route_id: "ROUTE_TIME_FIRST",
  profile: "TIME_FIRST",
  name: "Route Bravo (Direct Inshore - High Speed)",
  waypoints: [
    { lat: -64.82, lon: -63.5, leg_distance_km: 0, cumulative_distance_km: 0, risk_score: 22.0, estimated_speed_knots: 14.0, ice_concentration_pct: 18.0 },
    { lat: -65.5, lon: -60.0, leg_distance_km: 180.0, cumulative_distance_km: 180.0, risk_score: 31.5, estimated_speed_knots: 10.0, ice_concentration_pct: 54.0, note: "Near Larsen C front" },
    { lat: -68.0, lon: -54.0, leg_distance_km: 380.0, cumulative_distance_km: 560.0, risk_score: 28.0, estimated_speed_knots: 11.5, ice_concentration_pct: 46.0 },
    { lat: -75.58, lon: -26.55, leg_distance_km: 1402.7, cumulative_distance_km: 1962.7, risk_score: 21.0, estimated_speed_knots: 13.0, ice_concentration_pct: 22.0 }
  ],
  total_distance_km: 1962.7,
  total_distance_nm: 1059.8,
  estimated_duration_hours: 92.2,
  average_risk_score: 25.3,
  peak_risk_score: 31.5,
  fuel_estimate_tons: 98.8,
  major_hazards: ["High iceberg density", "Rapid compression risk inshore"],
  trade_offs: "Distance: 1059.8 NM | Est. Time: 92.2h | Peak Risk: 31.5/100",
  recommended: false,
  generated_at: new Date().toISOString()
};

export const ROUTE_CHARLIE: RouteCandidate = {
  route_id: "ROUTE_SAFETY_FIRST",
  profile: "SAFETY_FIRST",
  name: "Route Charlie (Offshore Deep Water - Maximum Safety)",
  waypoints: [
    { lat: -64.82, lon: -63.5, leg_distance_km: 0, cumulative_distance_km: 0, risk_score: 14.0, estimated_speed_knots: 12.0, ice_concentration_pct: 10.0 },
    { lat: -63.0, lon: -55.0, leg_distance_km: 450.0, cumulative_distance_km: 450.0, risk_score: 18.0, estimated_speed_knots: 12.5, ice_concentration_pct: 12.0 },
    { lat: -66.0, lon: -44.0, leg_distance_km: 580.0, cumulative_distance_km: 1030.0, risk_score: 22.0, estimated_speed_knots: 12.0, ice_concentration_pct: 20.0 },
    { lat: -75.58, lon: -26.55, leg_distance_km: 1255.4, cumulative_distance_km: 2285.4, risk_score: 20.0, estimated_speed_knots: 11.5, ice_concentration_pct: 15.0 }
  ],
  total_distance_km: 2285.4,
  total_distance_nm: 1234.0,
  estimated_duration_hours: 107.3,
  average_risk_score: 23.7,
  peak_risk_score: 27.6,
  fuel_estimate_tons: 113.9,
  major_hazards: ["Extended open swell endurance"],
  trade_offs: "Distance: 1234.0 NM | Est. Time: 107.3h | Peak Risk: 27.6/100",
  recommended: false,
  generated_at: new Date().toISOString()
};

export const FALLBACK_VOYAGE_PLAN: VoyagePlan = {
  vessel_id: "VESSEL-ATTENBOROUGH-PC5",
  origin: [-64.82, -63.5],
  destination: [-75.58, -26.55],
  destination_name: "Halley VI Research Station (Brunt Ice Shelf)",
  recommended_route: ROUTE_ALPHA,
  candidates: [ROUTE_ALPHA, ROUTE_BRAVO, ROUTE_CHARLIE],
  reroute_evaluation: {
    reassessment_triggered: false,
    trigger_reason: "Continuous baseline monitoring",
    recommended_route: ROUTE_ALPHA,
    alternative_routes: [ROUTE_BRAVO, ROUTE_CHARLIE],
    risk_delta: 3.9,
    explanation: "No immediate deviation required. Continuous monitoring active."
  },
  decision_explanation: {
    decision: "Recommend Route Alpha (Balanced - Recommended)",
    primary_evidence: [
      "Sea ice concentration along track within Polar Class PC5 design limits (<65.0%)",
      "Peak risk score capped at 27.6/100 vs 31.5/100 on high-speed inshore track",
      "Provides safe standoff distance (>25 NM) from active glacier calving front"
    ],
    risk_factors: {
      "Sea Ice Risk": 9.48,
      "Iceberg Density": 9.66,
      "Weather/Spray": 18.0
    },
    confidence_pct: 91.0,
    alternatives_considered: [
      "Route Bravo (Direct Inshore - High Speed) (1059.8 NM, Peak Risk 31.5)",
      "Route Charlie (Offshore Deep Water - Maximum Safety) (1234.0 NM, Peak Risk 27.6)"
    ],
    trade_off: "Distance: 1116.7 NM | Est. Time: 97.1h | Peak Risk: 27.6/100",
    recommended_action: "Adopt Route Alpha (Balanced - Recommended) as active track line. Transmit waypoint list to IBS bridge console."
  }
};

export const FALLBACK_ALERTS: Alert[] = [
  {
    alert_id: "ALERT-POLAR-001",
    severity: "WATCH",
    what: "Katabatic Wind Inflow & Sea-Ice Compression Expected in Western Weddell",
    where_lat: -65.8,
    where_lon: -61.2,
    where_location_name: "Western Weddell Sea / Larsen C Coastal Flank",
    when_timestamp: new Date().toISOString(),
    evidence: "Atmospheric gradient indicates 35-40 kt southwesterly katabatic gusts developing off the Antarctic Peninsula plateau over the next 12 hours.",
    confidence: 0.87,
    expected_development: "Pack ice will compress against shorefast ice edge, reducing open water leads from 18% to under 6%.",
    recommended_action: "Vessels in western leads should maneuver towards central basin open drift before compression intensifies.",
    acknowledged: false
  }
];

export const FALLBACK_GLACIERS = [
  {
    glacier_id: "GLACIER_LARSEN_C_FRONT",
    name: "Larsen C Ice Shelf - Northern Rifts",
    front_position: { lat: -66.2, lon: -60.5 },
    historical_baseline_front: { lat: -66.18, lon: -60.48 },
    velocity_m_per_day: 2.4,
    acceleration_m_per_day2: 0.05,
    retreat_distance_m: 120.0,
    calving_activity: "NORMAL_ABLATION",
    estimated_ice_loss_rate_gt_yr: 18.5,
    trend: "STEADY",
    confidence: 0.93,
    timestamp: new Date().toISOString()
  },
  {
    glacier_id: "GLACIER_BRUNT_ICE_SHELF",
    name: "Brunt Ice Shelf / Chasm 1",
    front_position: { lat: -75.55, lon: -26.8 },
    historical_baseline_front: { lat: -75.52, lon: -26.75 },
    velocity_m_per_day: 1.8,
    acceleration_m_per_day2: 0.02,
    retreat_distance_m: 65.0,
    calving_activity: "WATCH",
    estimated_ice_loss_rate_gt_yr: 8.2,
    trend: "STABLE",
    confidence: 0.89,
    timestamp: new Date().toISOString()
  }
];

export const FALLBACK_SATELLITE_FEATURES = {
  icebergs: [
    {
      iceberg_id: "BERG_A76A_RADAR",
      designation: "A-76A fragment",
      location: { lat: -65.45, lon: -58.2 },
      length_m: 3200,
      width_m: 1450,
      area_sq_km: 4.64,
      estimated_draft_m: 185.0,
      estimated_freeboard_m: 28.0,
      drift_velocity_knots: 0.85,
      drift_direction_deg: 42.0,
      confidence: 0.96,
      detected_sensor: "Sentinel-1 C-Band SAR (EW Mode)",
      timestamp: new Date().toISOString()
    },
    {
      iceberg_id: "BERG_TABULAR_02",
      designation: "Tabular Iceberg B-30 frag",
      location: { lat: -66.1, lon: -56.8 },
      length_m: 1800,
      width_m: 900,
      area_sq_km: 1.62,
      estimated_draft_m: 140.0,
      estimated_freeboard_m: 22.0,
      drift_velocity_knots: 1.1,
      drift_direction_deg: 55.0,
      confidence: 0.93,
      detected_sensor: "Sentinel-1 C-Band SAR (EW Mode)",
      timestamp: new Date().toISOString()
    }
  ],
  sea_ice: [
    {
      grid_id: "ICE_GRID_GERLACHE_SOUTH",
      bounds: { min_lat: -65.5, max_lat: -64.5, min_lon: -63.5, max_lon: -61.5 },
      center: { lat: -65.0, lon: -62.5 },
      concentration_pct: 42.0,
      stage: "first_year_pack",
      thickness_cm: 75.0,
      compression_risk: "LOW",
      confidence: 0.92,
      sensor_type: "Fused Sentinel-1 SAR & Sentinel-2 Optical",
      timestamp: new Date().toISOString()
    },
    {
      grid_id: "ICE_GRID_WEDDELL_NORTH",
      bounds: { min_lat: -67.0, max_lat: -65.5, min_lon: -61.5, max_lon: -57.0 },
      center: { lat: -66.25, lon: -59.25 },
      concentration_pct: 54.0,
      stage: "heavy_rafted_pack",
      thickness_cm: 110.0,
      compression_risk: "HIGH",
      confidence: 0.95,
      sensor_type: "Sentinel-1 SAR EW Mode",
      timestamp: new Date().toISOString()
    },
    {
      grid_id: "ICE_GRID_WEDDELL_OUTER",
      bounds: { min_lat: -66.5, max_lat: -64.5, min_lon: -56.0, max_lon: -50.0 },
      center: { lat: -65.5, lon: -53.0 },
      concentration_pct: 24.0,
      stage: "open_drift_ice",
      thickness_cm: 45.0,
      compression_risk: "LOW",
      confidence: 0.88,
      sensor_type: "Sentinel-1 SAR EW Mode",
      timestamp: new Date().toISOString()
    }
  ],
  glaciers: FALLBACK_GLACIERS,
  leads: [
    { lead_id: "LEAD_ALPHA", width_m: 450, orientation_deg: 140, navigable: true },
    { lead_id: "LEAD_BRAVO", width_m: 220, orientation_deg: 125, navigable: true }
  ],
  temporal_change: {
    glacier_or_region_id: "WEDDELL_PENINSULA_CORRIDOR",
    t0_timestamp: new Date(Date.now() - 5 * 86400000).toISOString(),
    t1_timestamp: new Date().toISOString(),
    delta_days: 5.0,
    sea_ice_concentration_delta_pct: 4.2,
    iceberg_count_delta: 1,
    front_displacement_m: -45.0,
    velocity_change_pct: 2.1,
    acceleration_detected: false,
    summary: "Cryosphere observation across 5.0 days indicates baseline equilibrium. Sea ice concentration increased marginally (+4.2%), front position displaced by -45.0m. No anomalous calving detected.",
    confidence: 0.94
  },
  scenario_stage: 0,
  fusion_provenance: "Sentinel-1 SAR + Sentinel-2 Optical Multi-Temporal Fusion [DEMO Mode | Confidence: 94.0%]"
};

export const FALLBACK_CHAT: ChatMessage[] = [
  {
    id: "MSG-001",
    role: "system",
    content: "DeLTa Multi-Agent Command Core initialized. Agents active: Navigation Agent, Hazard Sentinel, Perception Ingestion, IBS IBS Interface.",
    timestamp: new Date().toISOString()
  },
  {
    id: "MSG-002",
    role: "assistant",
    content: "Welcome to the DeLTa Antarctic Intelligence Console. Current active route is Route Alpha (Balanced Track, 1116.7 NM, Peak Risk: 27.6/100). All sensors synchronized.",
    timestamp: new Date().toISOString()
  }
];
