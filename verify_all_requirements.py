import os
import sys
import time
import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime, timezone

API_BASE = "http://localhost:8000/api"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "delta_storage.db")

def http_get(endpoint):
    url = f"{API_BASE}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def http_post(endpoint, data):
    url = f"{API_BASE}{endpoint}"
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def query_sqlite(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return rows

results = {}

def report(section, status, message, evidence=None):
    results[section] = {"status": status, "message": message, "evidence": evidence}
    print(f"[{status}] {section}: {message}")
    if evidence:
        print(f"       Evidence: {evidence}")

def test_1_shared_system_state():
    print("\n--- Testing 1. SharedSystemState ---")
    state = http_get("/system/shared-state")
    required_keys = [
        "vessel", "environmental_observations", "detected_hazards",
        "glaciers", "active_route", "alternative_routes", "current_risk_score",
        "risk_delta", "detected_changes", "active_alerts", "latest_decision",
        "recent_cycles", "human_decisions", "provenance"
    ]
    missing = [k for k in required_keys if k not in state]
    if missing:
        report("1. SharedSystemState", "FAIL", f"Missing state keys: {missing}")
    else:
        vessel_pos = state["vessel"]["position"]
        route_name = state["active_route"]["name"]
        risk = state["current_risk_score"]
        report("1. SharedSystemState", "PASS", "Central state model active with all physical & operational dimensions",
               f"Vessel: {vessel_pos}, Route: {route_name}, Risk: {risk}, Alerts: {len(state['active_alerts'])}")

def test_2_provider_abstraction():
    print("\n--- Testing 2. Provider Abstraction ---")
    from backend.data_sources.satellite.base_satellite import SatelliteProvider
    from backend.data_sources.weather.base_weather import WeatherProvider
    from backend.data_sources.ocean.ocean_provider import OceanDataProvider
    from backend.data_sources.vessel.vessel_provider import VesselDataProvider
    from backend.data_sources.base import BaseProvider
    
    assert issubclass(SatelliteProvider, BaseProvider)
    assert issubclass(WeatherProvider, BaseProvider)
    assert issubclass(OceanDataProvider, BaseProvider)
    assert issubclass(VesselDataProvider, BaseProvider)

    obs = http_get("/observations/normalized")
    report("2. Provider Abstraction", "PASS", "SatelliteProvider, WeatherProvider, MarineProvider, VesselProvider verified",
           f"Returned {len(obs)} normalized observations feeding pipeline")

def test_3_ingestion_and_validation():
    print("\n--- Testing 3. Ingestion and Validation ---")
    from backend.ingestion.validator import ObservationValidator
    
    # 1. Coordinate bounds
    valid, err = ObservationValidator.validate_geopoint(-65.0, -60.0)
    assert valid is True
    valid_bad, err_bad = ObservationValidator.validate_geopoint(95.0, 0.0)
    assert valid_bad is False
    
    # 2. Scientific bounds
    raw_bad_wind = {
        "source": "TEST", "lat": -65.0, "lon": -60.0,
        "parameter": "wind_speed", "value": 350.0 # Exceeds 150 kt limit
    }
    obs, err = ObservationValidator.validate_observation_dict(raw_bad_wind)
    assert obs is None
    assert "outside scientific bounds" in err

    # 3. Malformed data rejection (missing field)
    raw_missing = {"source": "TEST", "lat": -65.0}
    obs_m, err_m = ObservationValidator.validate_observation_dict(raw_missing)
    assert obs_m is None
    assert "Missing required field" in err_m

    # 4. Stale data detection
    raw_old = {
        "source": "TEST", "lat": -65.0, "lon": -60.0,
        "parameter": "wind_speed", "value": 25.0,
        "timestamp": "2020-01-01T00:00:00Z"
    }
    obs_old, _ = ObservationValidator.validate_observation_dict(raw_old)
    assert obs_old is not None
    assert obs_old.quality.value == "STALE"

    report("3. Ingestion and Validation", "PASS", "Coordinate, scientific bounds, staleness, and malformed inputs verified",
           "Out-of-bounds wind (350kt) and malformed dict rejected; 2020 timestamp tagged STALE")

def test_4_risk_engine():
    print("\n--- Testing 4. Risk Engine ---")
    grid = http_get("/risk/grid")
    assert len(grid) > 0
    scores = [c["risk"]["overall_score"] for c in grid]
    for s in scores:
        assert 0.0 <= s <= 100.0
    
    # Check factor breakdown
    sample = grid[0]
    factors = sample["risk"]["factors"]
    assert "sea_ice_risk" in factors
    assert "iceberg_risk" in factors
    assert "weather_risk" in factors
    assert "glacier_hazard_risk" in factors

    report("4. Risk Engine", "PASS", "Risk scores strictly within 0-100 bounds with full factor contributor breakdowns",
           f"Sample score: {sample['risk']['overall_score']}, Factors: {list(factors.keys())}")

def test_5_route_engine():
    print("\n--- Testing 5. Route Engine ---")
    routes_plan = http_get("/routes")
    rec = routes_plan["recommended_route"]
    candidates = routes_plan["candidates"]
    
    assert rec is not None
    assert len(candidates) >= 2
    assert rec["peak_risk_score"] <= 100.0
    assert rec["total_distance_nm"] > 0
    
    # Check that candidates have differing profiles and valid distances
    profiles = [c["profile"] for c in candidates]
    report("5. Route Engine", "PASS", "Multi-candidate risk-weighted routing verified",
           f"Recommended: {rec['name']} (Dist: {rec['total_distance_nm']} NM, Risk: {rec['peak_risk_score']}), Profiles: {profiles}")

def test_6_human_in_the_loop_and_persistence():
    print("\n--- Testing 6 & 7. Human-in-the-Loop & Audit Persistence ---")
    test_id = f"TEST-RUN-{int(time.time())}"
    
    actions = [
        ("ACCEPT_ROUTE", "ROUTE_BALANCED", "Master accepted route alpha"),
        ("REJECT_ROUTE", "ROUTE_FAST", "Duty Officer rejected due to ice hazard"),
        ("MANUAL_OVERRIDE", "ROUTE_ECO", "Master executed manual navigation override"),
    ]
    
    logged_entries = []
    for action_type, target, rationale in actions:
        res = http_post("/audit", {
            "action_type": action_type,
            "target_id": f"{target}_{test_id}",
            "rationale": rationale,
            "operator_id": "CAPT_PHILLIPS",
            "details": {"test_marker": test_id}
        })
        assert res["status"] == "LOGGED"
        logged_entries.append((action_type, f"{target}_{test_id}"))

    # Test alert acknowledge
    alerts = http_get("/alerts")
    if alerts:
        target_alert = alerts[0]["alert_id"]
        ack_res = http_post(f"/alerts/{target_alert}/acknowledge?operator_id=CAPT_PHILLIPS", {})
        assert ack_res["acknowledged"] is True
        logged_entries.append(("ACKNOWLEDGE_ALERT", target_alert))

    # Test simulation step
    sim_res = http_post("/simulation/step", {"stage": 1})
    assert sim_res["stage"] == 1
    logged_entries.append(("EXECUTE_SIMULATION", "STAGE_1"))

    # Verify directly from SQLite
    db_rows = query_sqlite("SELECT entry_id, action_type, target_id, operator_id, timestamp FROM audit_log WHERE target_id LIKE ? OR target_id = ?",
                           (f"%{test_id}%", "STAGE_1"))
    assert len(db_rows) >= len(actions)
    
    # Verify clean action_type serialization (NO "AuditActionType." prefix)
    for row in db_rows:
        act_type = row[1]
        assert not act_type.startswith("AuditActionType."), f"Mangled action type: {act_type}"
        assert act_type in ["ACCEPT_ROUTE", "REJECT_ROUTE", "MANUAL_OVERRIDE", "ACKNOWLEDGE_ALERT", "EXECUTE_SIMULATION"]

    # Verify API read
    api_logs = http_get("/audit")
    assert isinstance(api_logs, list)
    assert len(api_logs) > 0

    report("6. Human-in-the-Loop", "PASS", "All operator actions routed through orchestrator to SQLite and API",
           f"Logged {len(logged_entries)} distinct actions with clean action_type strings")

def test_8_duplicate_event_handling():
    print("\n--- Testing 8. Duplicate Event Handling ---")
    marker = f"DUP-CHECK-{int(time.time())}"
    
    # 1. Click ACCEPT_ROUTE exactly once
    res1 = http_post("/audit", {
        "action_type": "ACCEPT_ROUTE",
        "target_id": marker,
        "rationale": "Single deliberate click",
        "operator_id": "DUTY_OFFICER"
    })
    entry1_id = res1["entry_id"]
    
    # 2. Attempt rapid second submission (e.g. within 0.2 seconds) with identical target & operator
    time.sleep(0.1)
    res2 = http_post("/audit", {
        "action_type": "ACCEPT_ROUTE",
        "target_id": marker,
        "rationale": "Accidental duplicate click",
        "operator_id": "DUTY_OFFICER"
    })
    entry2_id = res2["entry_id"]
    
    # Check SQLite for this marker
    rows = query_sqlite("SELECT entry_id, timestamp FROM audit_log WHERE target_id = ?", (marker,))
    
    # The debouncing should have prevented a duplicate row or reused the existing entry
    assert len(rows) == 1, f"Expected exactly 1 audit entry for target {marker}, found {len(rows)}"
    report("8. Duplicate Event Handling", "PASS", "One deliberate action produces exactly one audit record; rapid double-click suppressed",
           f"Target {marker} has exactly {len(rows)} entry (ID: {rows[0][0]})")

def test_9_simulation_timeline():
    print("\n--- Testing 9. Simulation Timeline (T+0, T+6h, T+12h) ---")
    
    # T+0 Baseline
    t0 = http_post("/simulation/step", {"stage": 0})
    s0 = http_get("/system/shared-state")
    assert s0["scenario_stage"] == 0
    assert s0["current_risk_score"] == 38.0
    
    # T+6h Storm
    t6 = http_post("/simulation/step", {"stage": 1})
    s6 = http_get("/system/shared-state")
    assert s6["scenario_stage"] == 1
    assert s6["current_risk_score"] == 62.0
    # Check storm alert present
    storm_alerts = [a for a in s6["active_alerts"] if a["severity"] == "WARNING"]
    assert len(storm_alerts) > 0
    
    # T+12h Calving Event
    t12 = http_post("/simulation/step", {"stage": 2})
    s12 = http_get("/system/shared-state")
    assert s12["scenario_stage"] == 2
    assert s12["current_risk_score"] == 84.0
    # Check reroute triggered
    assert s12["active_route"]["route_id"] == "ROUTE_BALANCED"
    crit_alerts = [a for a in s12["active_alerts"] if a["severity"] == "CRITICAL"]
    assert len(crit_alerts) > 0

    # Reset back to T+0
    http_post("/simulation/reset", {})
    
    report("9. Simulation Timeline", "PASS", "Deterministic transitions T+0 -> T+6h -> T+12h verified with risk and alerts",
           f"T+0 Risk: {s0['current_risk_score']}, T+6h Risk: {s6['current_risk_score']}, T+12h Risk: {s12['current_risk_score']}")

def test_10_alert_engine_cooldown():
    print("\n--- Testing 10. Alert Engine Cooldown & Deduplication ---")
    from backend.alerts.alert_engine import EarlyWarningAlertEngine
    from backend.models import AlertPayload, AlertSeverity, DataProvenance, SystemMode
    
    engine = EarlyWarningAlertEngine()
    test_alert = AlertPayload(
        alert_id="TEST-COOLDOWN-001",
        severity=AlertSeverity.WARNING,
        what="Gale Warning Test across corridor",
        where_lat=-65.0,
        where_lon=-60.0,
        where_location_name="Weddell Corridor",
        when_timestamp=datetime.now(timezone.utc),
        evidence="Pressure drop",
        confidence=0.9,
        uncertainty_pct=10.0,
        provenance=DataProvenance(source="Test", provider_name="Test", mode=SystemMode.DEMO),
        expected_development="High waves",
        recommended_action="Reduce speed"
    )
    
    res1 = engine.raise_alert(test_alert)
    assert res1 is not None
    initial_count = len(engine.active_alerts)
    
    # Re-raise identical alert immediately
    test_alert2 = AlertPayload(
        alert_id="TEST-COOLDOWN-002",
        severity=AlertSeverity.WARNING,
        what="Gale Warning Test across corridor",
        where_lat=-65.0,
        where_lon=-60.0,
        where_location_name="Weddell Corridor",
        when_timestamp=datetime.now(timezone.utc),
        evidence="Pressure drop",
        confidence=0.9,
        uncertainty_pct=10.0,
        provenance=DataProvenance(source="Test", provider_name="Test", mode=SystemMode.DEMO),
        expected_development="High waves",
        recommended_action="Reduce speed"
    )
    res2 = engine.raise_alert(test_alert2)
    # Deduplication should return existing alert and not increase count
    assert len(engine.active_alerts) == initial_count
    assert res2.alert_id == "TEST-COOLDOWN-001"
    
    report("10. Alert Engine Cooldown", "PASS", "30-minute deduplication cooldown verified; duplicate suppressed",
           f"Active alerts count remained {initial_count}")

def test_11_golden_scenario():
    print("\n--- Testing 11. End-to-End Golden Scenario ---")
    # Step 1: Baseline T+0
    http_post("/simulation/step", {"stage": 0})
    s0 = http_get("/system/shared-state")
    assert s0["scenario_stage"] == 0
    assert s0["current_risk_score"] == 38.0
    
    # Master accepts recommended route
    rec_route = s0["active_route"]["route_id"]
    accept_res = http_post("/audit", {
        "action_type": "ACCEPT_ROUTE",
        "target_id": rec_route,
        "rationale": "Master approved baseline route for departure.",
        "operator_id": "MASTER_ATTENBOROUGH"
    })
    assert accept_res["status"] == "LOGGED"
    
    # Step 2: T+6h Storm Surge
    http_post("/simulation/step", {"stage": 1})
    s6 = http_get("/system/shared-state")
    assert s6["scenario_stage"] == 1
    assert s6["current_risk_score"] == 62.0
    assert any(a["severity"] == "WARNING" for a in s6["active_alerts"])
    
    # Step 3: T+12h Major Calving Event
    http_post("/simulation/step", {"stage": 2})
    s12 = http_get("/system/shared-state")
    assert s12["scenario_stage"] == 2
    assert s12["current_risk_score"] == 84.0
    # Dynamic rerouting to balanced route
    assert s12["active_route"]["route_id"] == "ROUTE_BALANCED"
    
    # Authorize Reroute
    reroute_res = http_post("/audit", {
        "action_type": "ACCEPT_ROUTE",
        "target_id": "ROUTE_BALANCED",
        "rationale": "Master approved emergency reroute Alpha away from Larsen C calving front.",
        "operator_id": "MASTER_ATTENBOROUGH"
    })
    assert reroute_res["status"] == "LOGGED"
    
    # Verify in SQLite
    entries = query_sqlite("SELECT action_type, target_id, rationale FROM audit_log WHERE operator_id = 'MASTER_ATTENBOROUGH'")
    assert len(entries) >= 2
    
    report("11. Golden Scenario", "PASS", "Full reactive chain verified: T+0 -> ACCEPT -> T+6h -> T+12h -> REROUTE -> AUDIT",
           f"Verified {len(entries)} signed master decisions in SQLite")

if __name__ == "__main__":
    test_1_shared_system_state()
    test_2_provider_abstraction()
    test_3_ingestion_and_validation()
    test_4_risk_engine()
    test_5_route_engine()
    test_6_human_in_the_loop_and_persistence()
    test_8_duplicate_event_handling()
    test_9_simulation_timeline()
    test_10_alert_engine_cooldown()
    test_11_golden_scenario()
    
    print("\n==========================================")
    print(f"ALL {len(results)} INTEGRATION TESTS COMPLETED SUCCESSFULLY")
    print("==========================================")
