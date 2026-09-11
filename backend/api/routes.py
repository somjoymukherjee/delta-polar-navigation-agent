"""
FastAPI Route Handlers for DeLTa Polar Intelligence Platform
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from backend.models import (
    GeoPoint, BoundingBox, SystemMode, AuditActionType, RoutingProfile
)
from backend.agents.orchestrator import orchestrator
from backend.agents.navigation_agent import navigation_agent
from backend.agents.hazard_agent import hazard_agent
from backend.data_sources.fusion import fusion_engine
from backend.perception.fusion_perception import perception_engine
from backend.risk_engine.risk_engine import risk_engine
from backend.alerts.alert_engine import alert_engine
from backend.simulation.simulator import simulator
from backend.database.db import db

router = APIRouter(prefix="/api")

# --- System & Status ---
@router.get("/status")
def get_system_status():
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    return {
        "system_name": "DeLTa Polar Intelligence Platform",
        "mode": orchestrator.system_mode.value,
        "current_step": orchestrator.current_step.value,
        "scenario_stage": simulator.stage,
        "scenario_name": simulator.scenario_name,
        "scenario_step_name": simulator.current_step_name,
        "last_cycle_timestamp": orchestrator.last_cycle_time.isoformat(),
        "active_alerts_count": len(alert_engine.get_alerts()),
        "vessel_name": vessel.profile.name,
        "polar_class": vessel.profile.polar_class.value,
        "coordinates": vessel.position.as_tuple(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@router.post("/mode")
def set_system_mode(mode: SystemMode):
    orchestrator.system_mode = mode
    fusion_engine.set_live_mode(live=(mode == SystemMode.LIVE))
    return {"status": "SUCCESS", "new_mode": mode.value}

# --- Central Source of Truth & Shared System State ---
@router.get("/system/shared-state")
def get_shared_system_state():
    if not orchestrator.shared_state:
        orchestrator.run_autonomous_cycle()
    return orchestrator.shared_state.model_dump() if orchestrator.shared_state else {}

@router.get("/agent/state")
def get_agent_state():
    if not orchestrator.shared_state:
        orchestrator.run_autonomous_cycle()
    return orchestrator.shared_state.model_dump() if orchestrator.shared_state else {}

@router.get("/agent/cycles")
def get_agent_cycles():
    return [c.model_dump() for c in orchestrator.cycle_records[-20:]]

@router.get("/agent/activity")
def get_agent_activity():
    return [item.model_dump() for item in orchestrator.activity_stream]

@router.get("/observations/normalized")
def get_normalized_observations():
    return [o.model_dump() for o in orchestrator.ingestion_pipeline.get_latest_observations()] or fusion_engine.get_normalized_observations()

@router.get("/risk/delta")
def get_risk_delta():
    if orchestrator.shared_state and orchestrator.shared_state.risk_delta:
        return orchestrator.shared_state.risk_delta.model_dump()
    if orchestrator.unified_state and orchestrator.unified_state.risk_delta:
        return orchestrator.unified_state.risk_delta.model_dump()
    return {
        "previous_score": 38.0,
        "current_score": 38.0,
        "delta": 0.0,
        "main_contributors": {},
        "explanation": "Nominal environmental equilibrium maintained."
    }

# --- Vessel Telemetry ---
@router.get("/vessel")
def get_vessel_state():
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    return vessel.model_dump()

class SetDestinationRequest(BaseModel):
    lat: float
    lon: float
    name: str

@router.post("/vessel/destination")
def set_destination(req: SetDestinationRequest):
    fusion_engine.vessel_provider.set_destination(req.lat, req.lon, req.name)
    orchestrator.run_autonomous_cycle()
    return {"status": "SUCCESS", "destination": req.model_dump()}

# --- Routes & Navigation ---
@router.get("/routes")
def get_routes():
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    plan = navigation_agent.plan_voyage(
        vessel=vessel,
        destination=vessel.destination or GeoPoint(lat=-75.58, lon=-26.50),
        perception_data=perception_engine.get_perception_state(BoundingBox(min_lat=-76, max_lat=-63, min_lon=-65, max_lon=-25), simulator.stage),
        weather_data=fusion_engine.weather_provider.get_current_conditions(vessel.position).model_dump(),
        scenario_stage=simulator.stage
    )
    return plan

class RecalculateRouteRequest(BaseModel):
    profile: Optional[RoutingProfile] = RoutingProfile.BALANCED
    destination_lat: Optional[float] = None
    destination_lon: Optional[float] = None

@router.post("/routes/recalculate")
def recalculate_route(req: RecalculateRouteRequest):
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    dest = vessel.destination
    if req.destination_lat and req.destination_lon:
        dest = GeoPoint(lat=req.destination_lat, lon=req.destination_lon)
    
    plan = navigation_agent.plan_voyage(
        vessel=vessel,
        destination=dest or GeoPoint(lat=-75.58, lon=-26.50),
        perception_data=perception_engine.get_perception_state(BoundingBox(min_lat=-76, max_lat=-63, min_lon=-65, max_lon=-25), simulator.stage),
        weather_data=fusion_engine.weather_provider.get_current_conditions(vessel.position).model_dump(),
        scenario_stage=simulator.stage
    )
    return plan

# --- Satellite & Computer Vision ---
@router.get("/satellite/passes")
def get_satellite_passes():
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    bounds = BoundingBox(
        min_lat=vessel.position.lat - 3.0,
        max_lat=vessel.position.lat + 3.0,
        min_lon=vessel.position.lon - 6.0,
        max_lon=vessel.position.lon + 6.0
    )
    passes = fusion_engine.satellite_provider.fetch_latest_passes(bounds, limit=4)
    return [p.model_dump() for p in passes]

@router.get("/satellite/temporal-change")
def get_temporal_change():
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    t0 = now - timedelta(days=5)
    res = perception_engine.temporal_engine.compare_observations(
        region_id="WEDDELL_PENINSULA_CORRIDOR",
        t0_time=t0,
        t1_time=now,
        scenario_stage=simulator.stage
    )
    return res.model_dump()

@router.get("/satellite/features")
def get_satellite_features():
    bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
    features = perception_engine.get_perception_state(bounds, scenario_stage=simulator.stage)
    return features

# --- Cryosphere & Glaciers ---
@router.get("/hazards/glaciers")
def get_glacier_hazards():
    bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
    perc = perception_engine.get_perception_state(bounds, scenario_stage=simulator.stage)
    results = []
    for g_dict in perc.get("glaciers", []):
        from backend.models import GlacierObservation
        obs = GlacierObservation(**g_dict)
        res = hazard_agent.analyze_glacier(obs, scenario_stage=simulator.stage)
        results.append(res)
    return results

# --- Risk Engine ---
@router.get("/risk/grid")
def get_risk_grid():
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    bounds = BoundingBox(
        min_lat=-68.0,
        max_lat=-63.0,
        min_lon=-64.0,
        max_lon=-52.0
    )
    perc = perception_engine.get_perception_state(bounds, scenario_stage=simulator.stage)
    weather = fusion_engine.weather_provider.get_current_conditions(vessel.position).model_dump()
    cells = risk_engine.generate_risk_grid(bounds, steps_lat=6, steps_lon=8, perception_data=perc, weather_data=weather)
    return [c.model_dump() for c in cells]

class EvaluatePointRequest(BaseModel):
    lat: float
    lon: float

@router.post("/risk/evaluate")
def evaluate_point_risk(req: EvaluatePointRequest):
    vessel = fusion_engine.vessel_provider.get_vessel_state()
    bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
    perc = perception_engine.get_perception_state(bounds, scenario_stage=simulator.stage)
    weather = fusion_engine.weather_provider.get_current_conditions(vessel.position).model_dump()
    score = risk_engine.evaluate_point(GeoPoint(lat=req.lat, lon=req.lon), vessel=vessel.profile, perception_data=perc, weather_data=weather)
    return score.model_dump()

# --- Alerts ---
@router.get("/alerts")
def get_alerts(severity: Optional[str] = None):
    return [a.model_dump() for a in alert_engine.get_alerts(severity_filter=severity)]

@router.post("/alerts/{alert_id}/acknowledge")
def acknowledge_alert(alert_id: str, operator_id: str = "DUTY_OFFICER"):
    res = alert_engine.acknowledge_alert(alert_id, operator_id=operator_id)
    if not res:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    orchestrator.handle_human_action(
        action_type=AuditActionType.ACKNOWLEDGE_ALERT,
        target_id=alert_id,
        details={"alert_id": alert_id},
        rationale=f"Operator {operator_id} acknowledged warning.",
        operator_id=operator_id
    )
    return res.model_dump()

# --- AI Chat & Tool Calling ---
class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
def post_chat_message(req: ChatRequest):
    msg = orchestrator.process_operator_message(req.message)
    return msg.model_dump()

@router.get("/chat/history")
def get_chat_history():
    return [m.model_dump() for m in orchestrator.chat_history]

# --- Simulation Engine ---
class SimulationStepRequest(BaseModel):
    stage: int

@router.post("/simulation/step")
def simulation_step(req: SimulationStepRequest):
    res = simulator.step_to_stage(req.stage)
    return res

@router.post("/simulation/calving-event")
def trigger_calving_event():
    res = simulator.trigger_sudden_calving_event()
    return res

@router.post("/simulation/reset")
def reset_simulation():
    res = simulator.reset()
    return res

# --- Human-in-the-Loop & Audit Log ---
class AuditLogRequest(BaseModel):
    action_type: str
    target_id: str
    rationale: str
    operator_id: Optional[str] = "DUTY_OFFICER"
    details: Optional[Dict[str, Any]] = None

@router.post("/audit")
def create_audit_entry(req: AuditLogRequest):
    clean_action = req.action_type.replace("AuditActionType.", "").strip()
    try:
        act_enum = AuditActionType(clean_action)
    except Exception:
        act_enum = AuditActionType.CONFIG_CHANGE

    entry = orchestrator.handle_human_action(
        action_type=act_enum,
        target_id=req.target_id,
        rationale=req.rationale,
        operator_id=req.operator_id or "DUTY_OFFICER",
        details=req.details or {}
    )
    return {"status": "LOGGED", "entry_id": entry.entry_id}

@router.get("/audit")
def get_audit_trail():
    return db.get_audit_logs(limit=50)
