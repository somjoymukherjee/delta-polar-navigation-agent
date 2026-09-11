"""
DeLTa Automated Test Suite
Tests Risk Engine, Route Optimizer, Perception Layer, Glacier Hazard Agent,
AI Orchestrator, and FastAPI endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import GeoPoint, BoundingBox, VesselProfile, PolarClass, RoutingProfile
from backend.risk_engine.risk_engine import CentralRiskEngine
from backend.route_optimizer.polar_router import PolarRouteOptimizer
from backend.perception.fusion_perception import PerceptionFusionEngine
from backend.agents.hazard_agent import GlacierHazardAgent
from backend.models import GlacierObservation
from backend.agents.orchestrator import AIOrchestrator
from datetime import datetime, timezone

client = TestClient(app)

def test_api_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["system_name"] == "DeLTa Polar Intelligence Platform"
    assert "mode" in data
    assert "current_step" in data

def test_risk_engine_evaluation():
    engine = CentralRiskEngine()
    vessel = VesselProfile(polar_class=PolarClass.PC5, safe_ice_concentration_limit=65.0)
    
    # Safe open polar water point
    safe_pt = GeoPoint(lat=-63.0, lon=-55.0)
    score_safe = engine.evaluate_point(safe_pt, vessel=vessel)
    assert 0.0 <= score_safe.overall_score <= 100.0
    assert score_safe.category.value in ["SAFE", "LOW", "MODERATE"]

    # Point directly in restricted ASPA zone (-63.3, -62.1)
    aspa_pt = GeoPoint(lat=-63.3, lon=-62.1)
    score_aspa = engine.evaluate_point(aspa_pt, vessel=vessel)
    assert score_aspa.overall_score >= 80.0
    assert score_aspa.factors.restricted_zone_penalty == 100.0

def test_route_optimizer_multi_candidates():
    router = PolarRouteOptimizer()
    origin = GeoPoint(lat=-64.82, lon=-63.50)
    destination = GeoPoint(lat=-75.58, lon=-26.50)
    vessel = VesselProfile()

    # Stage 0: baseline routes
    routes_stage0 = router.generate_candidate_routes(origin, destination, vessel, scenario_stage=0)
    assert len(routes_stage0) == 3
    profiles = [r.profile for r in routes_stage0]
    assert RoutingProfile.BALANCED in profiles
    assert RoutingProfile.TIME_FIRST in profiles
    assert RoutingProfile.SAFETY_FIRST in profiles

    # Check waypoints and distance calculation
    rec_route = next(r for r in routes_stage0 if r.recommended)
    assert rec_route.total_distance_km > 500.0
    assert rec_route.total_distance_nm > 250.0
    assert len(rec_route.waypoints) >= 4

    # Stage 1: Calving event - Route Bravo (Time-First) peak risk must surge
    routes_stage1 = router.generate_candidate_routes(origin, destination, vessel, scenario_stage=1)
    route_bravo = next(r for r in routes_stage1 if r.profile == RoutingProfile.TIME_FIRST)
    assert route_bravo.peak_risk_score >= 75.0
    assert route_bravo.recommended is False

def test_perception_temporal_change():
    engine = PerceptionFusionEngine()
    bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)

    # Baseline T0 state
    state_0 = engine.get_perception_state(bounds, scenario_stage=0)
    assert len(state_0["icebergs"]) >= 4
    assert len(state_0["glaciers"]) >= 1
    assert state_0["temporal_change"]["acceleration_detected"] is False

    # Dynamic calving stage
    state_1 = engine.get_perception_state(bounds, scenario_stage=1)
    assert len(state_1["icebergs"]) >= 7  # 3 new bergs
    assert state_1["temporal_change"]["acceleration_detected"] is True
    assert state_1["temporal_change"]["sea_ice_concentration_delta_pct"] > 15.0

def test_glacier_hazard_agent_scenarios():
    agent = GlacierHazardAgent()
    obs = GlacierObservation(
        glacier_id="TEST_LARSEN",
        name="Larsen C Test Front",
        front_position=GeoPoint(lat=-66.2, lon=-60.5),
        historical_baseline_front=GeoPoint(lat=-66.18, lon=-60.48),
        velocity_m_per_day=4.5,
        acceleration_m_per_day2=0.35,
        retreat_distance_m=800.0,
        calving_activity="MAJOR_CALVING_COLLAPSE",
        confidence=0.92,
        timestamp=datetime.now(timezone.utc)
    )

    analysis = agent.analyze_glacier(obs, scenario_stage=1)
    assert len(analysis["scenarios"]) == 3
    scenario_names = [s["scenario_name"] for s in analysis["scenarios"]]
    assert any("Baseline" in name for name in scenario_names)
    assert any("Accelerated" in name for name in scenario_names)
    assert any("High-Change" in name for name in scenario_names)

    assert len(analysis["downstream_hazards"]) >= 2
    assert analysis["recommended_alert"] is not None
    assert analysis["recommended_alert"]["severity"] == "CRITICAL"

def test_orchestrator_autonomous_loop_and_chat():
    orch = AIOrchestrator()
    cycle = orch.run_autonomous_cycle(force_stage=0)
    assert cycle["current_step"] == "MONITOR"
    assert "voyage_plan" in cycle
    assert "perception" in cycle

    # Test Chat Tool Execution
    msg1 = orch.process_operator_message("Why did you choose the recommended route?")
    assert msg1.role == "assistant"
    assert msg1.tool_calls is not None
    assert len(msg1.tool_calls) > 0
    assert msg1.decision_card is not None

    msg2 = orch.process_operator_message("Show latest satellite observations and icebergs")
    assert "Sentinel" in msg2.content or "iceberg" in msg2.content.lower()

def test_simulation_endpoints():
    # Advance to Stage 2
    r_step = client.post("/api/simulation/step", json={"stage": 2})
    assert r_step.status_code == 200
    assert r_step.json()["stage"] == 2

    # Query routes in Stage 2 (should reflect high risk & reroute)
    r_routes = client.get("/api/routes")
    assert r_routes.status_code == 200
    routes_data = r_routes.json()
    assert routes_data["reroute_evaluation"]["reassessment_triggered"] is True

    # Reset back to Stage 0
    r_reset = client.post("/api/simulation/reset")
    assert r_reset.status_code == 200
    assert r_reset.json()["stage"] == 0
