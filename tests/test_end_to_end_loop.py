"""
DeLTa End-to-End Autonomous Agent Loop Test
Verifies the complete causal chain:
Environmental Change -> Detection -> State Comparison -> Risk Update ->
Agent Reasoning -> Route Recalculation -> Alert -> Unified State Update
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import RoutingProfile, SystemMode

client = TestClient(app)

def test_full_autonomous_end_to_end_cycle():
    # 1. Start in baseline stage (T+0)
    r_reset = client.post("/api/simulation/reset")
    assert r_reset.status_code == 200
    assert r_reset.json()["stage"] == 0

    # Verify initial baseline state
    r_state0 = client.get("/api/agent/state")
    assert r_state0.status_code == 200
    state0 = r_state0.json()
    assert state0["current_risk_score"] < 60.0
    initial_route_id = state0["active_route"]["route_id"]

    # 2. TRIGGER ENVIRONMENTAL CHANGE: Major ice calving & pack-ice surge (Stage 2)
    r_calving = client.post("/api/simulation/calving-event")
    assert r_calving.status_code == 200
    assert r_calving.json()["stage"] == 2

    # 3. DETECTION & STATE COMPARISON: Verify temporal change detected
    r_temp = client.get("/api/satellite/temporal-change")
    assert r_temp.status_code == 200
    temp_data = r_temp.json()
    assert temp_data["acceleration_detected"] is True
    assert temp_data["front_displacement_m"] <= -500.0  # -820m detachment
    assert temp_data["sea_ice_concentration_delta_pct"] >= 20.0 # +25.5%

    # 4. RISK UPDATE & REASONING: Risk score must increase and itemized contributors provided
    r_delta = client.get("/api/risk/delta")
    assert r_delta.status_code == 200
    risk_delta = r_delta.json()
    assert risk_delta["delta"] > 0
    assert "Sea Ice Pack" in risk_delta["main_contributors"] or "Sea Ice" in risk_delta["main_contributors"]
    assert "explanation" in risk_delta

    # 5. ROUTE RECALCULATION & DYNAMIC REROUTING:
    r_routes = client.get("/api/routes")
    assert r_routes.status_code == 200
    plan = r_routes.json()
    reroute_eval = plan["reroute_evaluation"]
    assert reroute_eval["reassessment_triggered"] is True
    assert reroute_eval["risk_delta"] > 0
    # Recommended route must bypass dangerous calving zone
    assert plan["recommended_route"]["recommended"] is True
    assert plan["recommended_route"]["profile"] == RoutingProfile.BALANCED.value

    # 6. ALERT GENERATION: Critical alert must be present
    r_alerts = client.get("/api/alerts?severity=CRITICAL")
    assert r_alerts.status_code == 200
    critical_alerts = r_alerts.json()
    assert len(critical_alerts) >= 1
    calving_alert = next((a for a in critical_alerts if "Calving" in a["what"] or "Larsen" in a["what"]), None)
    assert calving_alert is not None
    assert calving_alert["confidence"] > 0.85
    assert len(calving_alert["recommended_action"]) > 10

    # 7. UNIFIED STATE CHECK: Agent state maintains single source of truth across all modules
    r_state1 = client.get("/api/agent/state")
    assert r_state1.status_code == 200
    state1 = r_state1.json()
    assert state1["current_risk_score"] >= 75.0
    assert state1["detected_changes"]["acceleration_detected"] is True
    assert state1["active_route"]["route_id"] == plan["recommended_route"]["route_id"]

    # 8. OPERATIONAL ACTIVITY LOG: Verify the timestamped stream captured every step
    r_activity = client.get("/api/agent/activity")
    assert r_activity.status_code == 200
    activities = r_activity.json()
    steps_logged = [item["step"] for item in activities]
    for required_step in ["OBSERVE", "PERCEIVE", "COMPARE", "REASON", "PLAN"]:
        assert required_step in steps_logged

    # 9. HUMAN-IN-THE-LOOP AUDIT: Log an operator action and verify traceability
    r_audit = client.post("/api/audit", json={
        "action_type": "ACCEPT_ROUTE",
        "target_id": plan["recommended_route"]["route_id"],
        "rationale": "Officer accepted AI route recommendation after verifying radar imagery.",
        "operator_id": "CHIEF_OFFICER_ROSS"
    })
    assert r_audit.status_code == 200
    
    r_logs = client.get("/api/audit")
    assert r_logs.status_code == 200
    assert any(log["target_id"] == plan["recommended_route"]["route_id"] for log in r_logs.json())

    # Clean up: Return to baseline stage
    client.post("/api/simulation/reset")
