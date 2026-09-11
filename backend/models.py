"""
DeLTa (Dynamic Environmental & Logistics/Navigation Intelligence Agent)
Core Data Models and Type Definitions
"""

from __future__ import annotations
from enum import Enum
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SystemMode(str, Enum):
    LIVE = "LIVE"
    DEMO = "DEMO"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"

class DataQualityStatus(str, Enum):
    GOOD = "GOOD"
    DEGRADED = "DEGRADED"
    STALE = "STALE"
    UNVERIFIED = "UNVERIFIED"

class PolarClass(str, Enum):
    PC1 = "PC1"  # Year-round in all polar waters
    PC2 = "PC2"  # Year-round in moderate multi-year ice
    PC3 = "PC3"  # Year-round in second-year ice
    PC4 = "PC4"  # Year-round in thick first-year ice
    PC5 = "PC5"  # Year-round in medium first-year ice
    PC6 = "PC6"  # Summer/autumn in medium first-year ice
    PC7 = "PC7"  # Summer/autumn in thin first-year ice
    ICEBREAKER = "ICEBREAKER"
    OPEN_WATER = "OPEN_WATER"

class RoutingProfile(str, Enum):
    SAFETY_FIRST = "SAFETY_FIRST"
    BALANCED = "BALANCED"
    TIME_FIRST = "TIME_FIRST"
    FUEL_EFFICIENCY = "FUEL_EFFICIENCY"

class RiskCategory(str, Enum):
    SAFE = "SAFE"          # 0 - 20
    LOW = "LOW"            # 21 - 40
    MODERATE = "MODERATE"  # 41 - 60
    HIGH = "HIGH"          # 61 - 80
    EXTREME = "EXTREME"    # 81 - 100

class AlertSeverity(str, Enum):
    NORMAL = "NORMAL"
    WATCH = "WATCH"
    ADVISORY = "ADVISORY"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"

class HazardSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class HazardProbability(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"

class PhysicalMechanismType(str, Enum):
    CALVING_DETACHMENT = "CALVING_DETACHMENT"
    ICE_SHELF_RIFT = "ICE_SHELF_RIFT"
    DISPLACEMENT_WAVE = "DISPLACEMENT_WAVE"
    GLACIAL_LAKE_OUTBURST = "GLACIAL_LAKE_OUTBURST"
    MELTWATER_DRAINAGE = "MELTWATER_DRAINAGE"
    ICE_DAM_FAILURE = "ICE_DAM_FAILURE"
    ICE_COMPRESSION_SURGE = "ICE_COMPRESSION_SURGE"

class ObservationClassification(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    PROJECTED = "PROJECTED"

class AgentStep(str, Enum):
    OBSERVE = "OBSERVE"
    COLLECT = "COLLECT"
    VALIDATE = "VALIDATE"
    PERCEIVE = "PERCEIVE"
    REASON = "REASON"
    PLAN = "PLAN"
    ACT = "ACT"
    MONITOR = "MONITOR"

# ---------------------------------------------------------------------------
# Geospatial Primitives
# ---------------------------------------------------------------------------

class GeoPoint(BaseModel):
    lat: float = Field(..., description="Latitude [-90.0 to 90.0]")
    lon: float = Field(..., description="Longitude [-180.0 to 180.0]")

    def as_tuple(self) -> Tuple[float, float]:
        return (self.lat, self.lon)

class BoundingBox(BaseModel):
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float

# ---------------------------------------------------------------------------
# Data Quality & Provenance
# ---------------------------------------------------------------------------

class DataQualityReport(BaseModel):
    source: str
    sensor_type: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    age_seconds: float = 0.0
    spatial_resolution_km: float = 1.0
    quality: DataQualityStatus = DataQualityStatus.GOOD
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    processing_status: str = "COMPLETED"
    is_live: bool = False

class DataProvenance(BaseModel):
    source: str = "DeLTa Sensor Network"
    provider_name: str = "DemoSatelliteProvider"
    mode: SystemMode = SystemMode.DEMO
    is_simulated: bool = True
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    spatial_resolution_km: float = 1.0
    temporal_resolution_hours: float = 12.0
    quality: DataQualityStatus = DataQualityStatus.GOOD
    confidence: float = Field(0.92, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(8.0, ge=0.0, le=100.0)
    processing_stage: str = "VALIDATED"
    notes: Optional[str] = None


# ---------------------------------------------------------------------------
# Vessel Telemetry & Profile
# ---------------------------------------------------------------------------

class VesselProfile(BaseModel):
    vessel_id: str = "POLAR_EXPLORER_I"
    name: str = "R/V Sir David Attenborough"
    polar_class: PolarClass = PolarClass.PC5
    max_speed_knots: float = 15.0
    cruise_speed_knots: float = 11.5
    ice_breaking_capability_m: float = 1.0  # meters of level first-year ice
    length_m: float = 129.0
    beam_m: float = 24.0
    draft_m: float = 7.0
    fuel_rate_tons_per_day: float = 22.0
    safe_ice_concentration_limit: float = 65.0  # Max percentage for normal operations

class VesselState(BaseModel):
    profile: VesselProfile = Field(default_factory=VesselProfile)
    position: GeoPoint
    heading_deg: float = 0.0
    speed_knots: float = 0.0
    destination: Optional[GeoPoint] = None
    destination_name: Optional[str] = None
    current_route_id: Optional[str] = None
    status: str = "UNDERWAY"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ---------------------------------------------------------------------------
# Environmental Observations
# ---------------------------------------------------------------------------

class WeatherObservation(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    position: GeoPoint
    air_temp_c: float = -5.0
    wind_speed_knots: float = 18.0
    wind_gust_knots: float = 25.0
    wind_direction_deg: float = 220.0
    wave_height_m: float = 2.5
    wave_period_s: float = 8.0
    visibility_nm: float = 8.0
    freezing_spray_risk: str = "MODERATE"  # LOW, MODERATE, SEVERE
    barometric_pressure_hpa: float = 984.0
    quality: DataQualityReport = Field(default_factory=lambda: DataQualityReport(source="OpenMeteo-Polar"))

class OceanObservation(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    position: GeoPoint
    sea_surface_temp_c: float = -1.2
    current_speed_knots: float = 0.8
    current_direction_deg: float = 45.0
    salinity_psu: float = 34.0
    depth_m: float = 850.0
    quality: DataQualityReport = Field(default_factory=lambda: DataQualityReport(source="Copernicus-Marine"))

# ---------------------------------------------------------------------------
# Satellite & Computer Vision Features
# ---------------------------------------------------------------------------

class IcebergDetection(BaseModel):
    id: str
    position: GeoPoint
    length_m: float
    width_m: float
    area_sqm: float
    estimated_height_m: float = 15.0
    drift_speed_knots: float = 0.4
    drift_direction_deg: float = 60.0
    confidence: float = Field(..., ge=0.0, le=1.0)
    detected_sensor: str = "Sentinel-1 SAR"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SeaIceObservation(BaseModel):
    grid_id: str
    bounds: BoundingBox
    center: GeoPoint
    concentration_pct: float = Field(..., ge=0.0, le=100.0)
    stage: str = "first_year_pack"  # open_water, grease_ice, thin_first_year, thick_first_year, fast_ice
    thickness_cm: float = 80.0
    compression_risk: str = "LOW"  # LOW, MEDIUM, HIGH
    confidence: float = 0.90
    sensor_type: str = "Sentinel-1 SAR / Sentinel-2 Fused"
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class GlacierObservation(BaseModel):
    glacier_id: str
    name: str
    front_position: GeoPoint
    historical_baseline_front: GeoPoint
    velocity_m_per_day: float
    acceleration_m_per_day2: float
    retreat_distance_m: float
    calving_activity: str = "MODERATE"  # LOW, MODERATE, HIGH, CALVING_EVENT
    estimated_ice_loss_rate_gt_yr: float = 12.4
    trend: str = "ACCELERATING"
    confidence: float = 0.91
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class SatelliteProduct(BaseModel):
    image_id: str
    provider: str  # Sentinel-1, Sentinel-2, Landsat-9, Mock
    sensor_type: str  # SAR, OPTICAL
    acquisition_time: datetime
    bounds: BoundingBox
    cloud_cover_pct: float = 0.0
    resolution_m: float = 10.0
    preview_url: Optional[str] = None
    processed_features: Dict[str, Any] = Field(default_factory=dict)
    quality: DataQualityReport

class TemporalChangeAnalysis(BaseModel):
    glacier_or_region_id: str
    t0_timestamp: datetime
    t1_timestamp: datetime
    delta_days: float
    sea_ice_concentration_delta_pct: float
    iceberg_count_delta: int
    front_displacement_m: float
    velocity_change_pct: float
    acceleration_detected: bool
    summary: str
    confidence: float

# ---------------------------------------------------------------------------
# Central Risk Engine
# ---------------------------------------------------------------------------

class RiskFactorBreakdown(BaseModel):
    sea_ice_risk: float = 0.0      # 0 - 100
    iceberg_risk: float = 0.0      # 0 - 100
    weather_risk: float = 0.0      # 0 - 100
    wave_risk: float = 0.0         # 0 - 100
    glacier_hazard_risk: float = 0.0 # 0 - 100
    restricted_zone_penalty: float = 0.0 # 0 or 100
    data_freshness_penalty: float = 0.0  # 0 - 20
    model_uncertainty_penalty: float = 0.0 # 0 - 15

class RiskScore(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    category: RiskCategory
    primary_driver: str
    factors: RiskFactorBreakdown
    explanation: str
    confidence: float = Field(0.92, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(8.0, ge=0.0, le=100.0)
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RiskGridCell(BaseModel):
    cell_id: str
    center: GeoPoint
    bounds: BoundingBox
    risk: RiskScore

# ---------------------------------------------------------------------------
# Navigation & Routing
# ---------------------------------------------------------------------------

class RouteWaypoint(BaseModel):
    lat: float
    lon: float
    leg_distance_km: float = 0.0
    cumulative_distance_km: float = 0.0
    risk_score: float = 0.0
    estimated_speed_knots: float = 12.0
    ice_concentration_pct: float = 0.0
    note: Optional[str] = None

class RouteCandidate(BaseModel):
    route_id: str
    profile: RoutingProfile
    name: str
    waypoints: List[RouteWaypoint]
    total_distance_km: float
    total_distance_nm: float
    estimated_duration_hours: float
    average_risk_score: float
    peak_risk_score: float
    fuel_estimate_tons: float
    major_hazards: List[str]
    trade_offs: str
    recommended: bool = False
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(10.0, ge=0.0, le=100.0)
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RerouteEvaluation(BaseModel):
    reassessment_triggered: bool
    trigger_reason: str
    old_route_id: Optional[str] = None
    recommended_route: RouteCandidate
    alternative_routes: List[RouteCandidate]
    risk_delta: float
    explanation: str

# ---------------------------------------------------------------------------
# Glacier Scenario Projections & Downstream Hazard Matrix
# ---------------------------------------------------------------------------

class GlacierScenarioProjection(BaseModel):
    scenario_name: str  # Baseline Scenario, Accelerated Warming, High-Change Extreme
    description: str
    annual_ice_loss_range_gt: Tuple[float, float]
    retreat_velocity_range_m_yr: Tuple[float, float]
    estimated_shelf_destabilization_window_years: Tuple[float, float]
    confidence: float = Field(0.85, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(15.0, ge=0.0, le=100.0)
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    assumptions: List[str]

class DownstreamHazardAssessment(BaseModel):
    hazard_type: str  # Iceberg / Calving Hazard, Ice-Shelf Instability, Calving Tsunami Wave, Glacial Lake Outburst, Coastal Inundation
    severity: HazardSeverity
    probability: HazardProbability
    physical_mechanism: PhysicalMechanismType = PhysicalMechanismType.CALVING_DETACHMENT
    observation_classification: ObservationClassification = ObservationClassification.OBSERVED
    confidence: float = Field(0.90, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(10.0, ge=0.0, le=100.0)
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    time_horizon: str  # "Immediate (0-6 hours)", "Short-term (1-3 days)", "Seasonal"
    affected_area_bounds: BoundingBox
    downstream_impact_summary: str
    recommended_action: str

# ---------------------------------------------------------------------------
# Alerts & Early Warning
# ---------------------------------------------------------------------------

class AlertPayload(BaseModel):
    alert_id: str
    severity: AlertSeverity
    what: str
    where_lat: float
    where_lon: float
    where_location_name: str
    when_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    evidence: str
    confidence: float = Field(0.92, ge=0.0, le=1.0)
    uncertainty_pct: float = Field(8.0, ge=0.0, le=100.0)
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    expected_development: str
    recommended_action: str
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

# ---------------------------------------------------------------------------
# Human-in-the-Loop & Audit Log
# ---------------------------------------------------------------------------

class AuditActionType(str, Enum):
    ACCEPT_ROUTE = "ACCEPT_ROUTE"
    REJECT_ROUTE = "REJECT_ROUTE"
    MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
    ACKNOWLEDGE_ALERT = "ACKNOWLEDGE_ALERT"
    EXECUTE_SIMULATION = "EXECUTE_SIMULATION"
    CONFIG_CHANGE = "CONFIG_CHANGE"

class AuditLogEntry(BaseModel):
    entry_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    operator_id: str = "DUTY_OFFICER"
    action_type: AuditActionType
    target_id: str
    details: Dict[str, Any]
    rationale: str

# ---------------------------------------------------------------------------
# Orchestrator & Chat
# ---------------------------------------------------------------------------

class DecisionExplanation(BaseModel):
    decision: str
    primary_evidence: List[str]
    risk_factors: Dict[str, float]
    confidence_pct: float
    alternatives_considered: List[str]
    trade_off: str
    recommended_action: str

class ChatMessage(BaseModel):
    id: str
    role: str  # user, assistant, system
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tool_calls: Optional[List[Dict[str, Any]]] = None
    decision_card: Optional[DecisionExplanation] = None

class AgentLoopState(BaseModel):
    current_step: AgentStep = AgentStep.MONITOR
    last_cycle_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active_scenario: str = "Weddell Sea Calving & Pack Ice Shift"
    mode: SystemMode = SystemMode.DEMO
    vessel_status: str = "En Route - Gerlache to Halley Station"
    active_alerts_count: int = 0
    route_status: str = "Active - Recalculated due to Ice Fracture"
    data_freshness_overall: str = "Optimal (4.2m ago)"

# ---------------------------------------------------------------------------
# Central Source of Truth & Normalized Observations
# ---------------------------------------------------------------------------

class NormalizedObservation(BaseModel):
    source: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    lat: float
    lon: float
    parameter: str  # e.g., sea_ice_concentration, iceberg_count, flow_velocity, wind_speed, wave_height
    value: float
    unit: str        # %, count, m/day, knots, meters, hPa
    confidence: float = Field(..., ge=0.0, le=1.0)
    uncertainty_pct: float = 8.0
    freshness_seconds: float = 0.0
    quality: DataQualityStatus = DataQualityStatus.GOOD
    mode: SystemMode = SystemMode.DEMO
    provenance: DataProvenance = Field(default_factory=DataProvenance)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RiskDeltaBreakdown(BaseModel):
    previous_score: float
    current_score: float
    delta: float
    main_contributors: Dict[str, float]  # e.g. {"Sea Ice": 18.0, "Iceberg Density": 7.0, "Weather": 4.0}
    explanation: str

class AgentActivityLogItem(BaseModel):
    id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_display: str
    step: str  # OBSERVE, PERCEIVE, COMPARE, REASON, PLAN, ACT, ALERT, MONITOR
    action: str
    details: Optional[Dict[str, Any]] = None

class AgentCycleRecord(BaseModel):
    cycle_id: str
    cycle_number: int
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: SystemMode = SystemMode.DEMO
    stage: AgentStep
    inputs_summary: Dict[str, Any]
    perceptions_summary: Dict[str, Any]
    risk_evaluation: Dict[str, Any]
    decisions_summary: Dict[str, Any]
    alerts_generated: List[str]
    confidence: float
    execution_duration_ms: float

class SharedSystemState(BaseModel):
    state_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: SystemMode = SystemMode.DEMO
    scenario_stage: int = 0
    current_step: AgentStep = AgentStep.MONITOR
    vessel: VesselState
    previous_vessel: Optional[VesselState] = None
    environmental_observations: List[NormalizedObservation] = Field(default_factory=list)
    previous_environmental_observations: Optional[List[NormalizedObservation]] = None
    detected_hazards: List[Dict[str, Any]] = Field(default_factory=list)
    glaciers: List[Dict[str, Any]] = Field(default_factory=list)
    active_route: RouteCandidate
    previous_route: Optional[RouteCandidate] = None
    alternative_routes: List[RouteCandidate] = Field(default_factory=list)
    current_risk_score: float = 38.0
    previous_risk_score: float = 38.0
    risk_delta: Optional[RiskDeltaBreakdown] = None
    detected_changes: Dict[str, Any] = Field(default_factory=dict)
    active_alerts: List[AlertPayload] = Field(default_factory=list)
    latest_decision: Optional[DecisionExplanation] = None
    recent_cycles: List[AgentCycleRecord] = Field(default_factory=list)
    human_decisions: List[Dict[str, Any]] = Field(default_factory=list)
    data_freshness_seconds: float = 45.0
    overall_confidence: float = 0.92
    uncertainty_pct: float = 8.0
    provenance: DataProvenance = Field(default_factory=DataProvenance)

class UnifiedAgentState(BaseModel):
    state_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    mode: SystemMode = SystemMode.DEMO
    current_step: AgentStep = AgentStep.MONITOR
    vessel: VesselState
    active_route: RouteCandidate
    previous_route: Optional[RouteCandidate] = None
    current_risk_score: float = 38.0
    previous_risk_score: float = 38.0
    risk_delta: Optional[RiskDeltaBreakdown] = None
    detected_changes: Dict[str, Any] = Field(default_factory=dict)
    active_alerts: List[AlertPayload] = Field(default_factory=list)
    latest_decision: Optional[DecisionExplanation] = None
    data_freshness_seconds: float = 45.0
    overall_confidence: float = 0.92
    uncertainty_pct: float = 8.0
    provenance: DataProvenance = Field(default_factory=DataProvenance)


