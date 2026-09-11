"""
Verification Suite for 5 Additional System Requirements & Golden End-to-End Scenario
1. DEMO/LIVE Data Integrity
2. Deterministic Core + AI Reasoning
3. Confidence Propagation
4. Live/NASA Future Provider Abstraction
5. Golden End-to-End Scenario
"""

import pytest
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import (
    SystemMode, GeoPoint, BoundingBox, VesselProfile, AuditActionType
)
from backend.risk_engine.risk_engine import CentralRiskEngine
from backend.route_optimizer.polar_router import PolarRouteOptimizer
from backend.perception.temporal_engine import TemporalChangeEngine
from backend.data_sources.base import FutureNASAEarthdataProvider, FutureCopernicusMarineProvider
from backend.agents.orchestrator import AIOrchestrator
from backend.simulation.simulator import PolarSimulator
from backend.ingestion.validator import ObservationValidator

client = TestClient(app)

# ---------------------------------------------------------------------------
# Requirement 1: DEMO/LIVE Data Integrity
# ---------------------------------------------------------------------------
def test_demo_live_provenance_integrity():
    """Verify that every observation, risk calculation, route, and alert has explicit DEMO provenance."""
    orch = AIOrchestrator()
    orch.run_autonomous_cycle(force_stage=0)

    state = orch.shared_state
    assert state is not None
    assert state.mode == SystemMode.DEMO
    assert state.provenance.mode == SystemMode.DEMO
    assert state.provenance.is_simulated is True

    # Check observations
    for obs in state.environmental_observations:
        assert obs.mode == SystemMode.DEMO
        assert obs.provenance.is_simulated is True
        assert obs.provenance.mode == SystemMode.DEMO

    # Check active route provenance
    assert state.active_route.provenance.mode == SystemMode.DEMO
    assert state.active_route.provenance.is_simulated is True

    # Check alerts provenance
    for alert in state.active_alerts:
        assert alert.provenance.mode == SystemMode.DEMO
        assert alert.provenance.is_simulated is True

# ---------------------------------------------------------------------------
# Requirement 2: Deterministic Core + AI Reasoning
# ---------------------------------------------------------------------------
def test_deterministic_core_calculations():
    """Verify that scientific calculations and routing are 100% deterministic."""
    risk_engine = CentralRiskEngine()
    vessel = VesselProfile()
    pt = GeoPoint(lat=-65.9, lon=-60.2)

    # Run twice with identical inputs
    score1 = risk_engine.evaluate_point(pt, vessel=vessel)
    score2 = risk_engine.evaluate_point(pt, vessel=vessel)
    assert score1.overall_score == score2.overall_score
    assert score1.factors.sea_ice_risk == score2.factors.sea_ice_risk
    assert score1.factors.iceberg_risk == score2.factors.iceberg_risk

    # Route optimizer determinism
    router = PolarRouteOptimizer()
    origin = GeoPoint(lat=-64.82, lon=-63.50)
    dest = GeoPoint(lat=-75.58, lon=-26.50)
    routes1 = router.generate_candidate_routes(origin, dest, vessel, scenario_stage=0)
    routes2 = router.generate_candidate_routes(origin, dest, vessel, scenario_stage=0)
    assert routes1[0].total_distance_km == routes2[0].total_distance_km
    assert routes1[0].peak_risk_score == routes2[0].peak_risk_score

    # Kinematics rule: if observations < 2, return INSUFFICIENT_DATA with confidence 0.0
    tc_engine = TemporalChangeEngine()
    now = datetime.now(timezone.utc)
    insufficient = tc_engine.compute_kinematics([(GeoPoint(lat=-65.0, lon=-60.0), now)])
    assert insufficient["status"] == "INSUFFICIENT_DATA"
    assert insufficient["confidence"] == 0.0

    # True kinematics calculation with N >= 2
    p0 = GeoPoint(lat=-65.0, lon=-60.0)
    p1 = GeoPoint(lat=-65.01, lon=-60.0)
    t0 = now - timedelta(days=2)
    t1 = now
    kinematics = tc_engine.compute_kinematics([(p0, t0), (p1, t1)])
    assert kinematics["status"] == "COMPLETED"
    assert kinematics["displacement_m"] > 0.0
    assert kinematics["velocity_m_per_day"] > 0.0
    assert kinematics["confidence"] > 0.80

# ---------------------------------------------------------------------------
# Requirement 3: Confidence Propagation
# ---------------------------------------------------------------------------
def test_confidence_propagation():
    """Verify confidence and uncertainty bounds from observation through decisions."""
    orch = AIOrchestrator()
    orch.run_autonomous_cycle(force_stage=0)
    state = orch.shared_state

    # Overall system confidence
    assert 0.0 <= state.overall_confidence <= 1.0
    assert 0.0 <= state.uncertainty_pct <= 100.0
    assert round(state.overall_confidence * 100.0 + state.uncertainty_pct, 0) == 100.0

    # Observation validator bounds
    raw_good = {
        "source": "Sentinel-1 SAR",
        "lat": -65.5,
        "lon": -62.0,
        "parameter": "sea_ice_concentration",
        "value": 45.0,
        "unit": "%",
        "confidence": 0.95
    }
    norm_obs, err = ObservationValidator.validate_observation_dict(raw_good)
    assert err is None
    assert norm_obs is not None
    assert norm_obs.confidence <= 0.95
    assert norm_obs.uncertainty_pct == round((1.0 - norm_obs.confidence) * 100.0, 1)

# ---------------------------------------------------------------------------
# Requirement 4: Live/NASA Future Provider Abstraction
# ---------------------------------------------------------------------------
def test_future_provider_abstractions():
    """Verify provider interface specifications for future NASA/Copernicus plug-in."""
    nasa = FutureNASAEarthdataProvider()
    status = nasa.get_health_status()
    assert status["status"] == "READY_FOR_INTEGRATION"
    assert status["is_live"] is False
    assert "NASA-Earthdata-CMR" in status["provider"]

    cmems = FutureCopernicusMarineProvider()
    cmems_status = cmems.get_health_status()
    assert cmems_status["status"] == "READY_FOR_INTEGRATION"
    assert cmems_status["is_live"] is False

# ---------------------------------------------------------------------------
# Requirement 5: Golden End-to-End Scenario
# ---------------------------------------------------------------------------
def test_golden_end_to_end_scenario():
    """
    Execute complete deterministic scenario chain:
    T+0 Baseline -> T+6h Storm -> T+12h Calving Event -> Reroute -> Alert -> Human Accept -> Audit.
    """
    sim = PolarSimulator()

    # 1. T+0 BASELINE
    t0_res = sim.step_to_stage(0)
    assert t0_res["stage"] == 0
    t0_cycle = t0_res["cycle_result"]
    assert t0_cycle["current_step"] == "MONITOR"
    assert t0_cycle["current_risk_score"] <= 45.0

    # 2. T+6h STORM
    t6_res = sim.step_to_stage(1)
    assert t6_res["stage"] == 1
    t6_cycle = t6_res["cycle_result"]
    # Environmental change detected
    assert t6_cycle["current_risk_score"] > t0_cycle["current_risk_score"]
    # Warning alert raised for storm
    storm_alerts = [a for a in t6_cycle["active_alerts"] if "Storm" in a["what"] or a["severity"] in ["WARNING", "WATCH"]]
    assert len(storm_alerts) >= 1

    # 3. T+12h CALVING EVENT
    t12_res = sim.step_to_stage(2)
    assert t12_res["stage"] == 2
    t12_cycle = t12_res["cycle_result"]
    
    # Risk threshold exceeded on inshore route -> reroute recommended
    assert t12_cycle["current_risk_score"] >= 80.0
    voyage_plan = t12_cycle["voyage_plan"]
    assert voyage_plan["reroute_evaluation"]["reassessment_triggered"] is True
    assert voyage_plan["recommended_route"]["route_id"] == "ROUTE_BALANCED"
    assert voyage_plan["recommended_route"]["recommended"] is True

    # Critical alert generated
    crit_alerts = [a for a in t12_cycle["active_alerts"] if a["severity"] == "CRITICAL"]
    assert len(crit_alerts) >= 1

    # 4. Human ACCEPT / REJECT / OVERRIDE decision
    audit_resp = client.post("/api/audit", json={
        "action_type": "ACCEPT_ROUTE",
        "target_id": voyage_plan["recommended_route"]["route_id"],
        "rationale": "Master of vessel approved Route Alpha following Larsen C calving notification.",
        "operator_id": "CAPT_ARMSTRONG"
    })
    assert audit_resp.status_code == 200
    audit_json = audit_resp.json()
    assert audit_json["status"] == "LOGGED"

    # 5. Verify audit log entry and shared system state
    shared_resp = client.get("/api/system/shared-state")
    assert shared_resp.status_code == 200
    shared_state = shared_resp.json()
    assert shared_state["scenario_stage"] == 2
    assert shared_state["current_step"] == "MONITOR"
    assert len(shared_state["human_decisions"]) >= 1
    assert shared_state["human_decisions"][-1]["action_type"] == "ACCEPT_ROUTE"
