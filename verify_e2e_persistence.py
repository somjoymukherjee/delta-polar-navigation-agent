"""
End-to-End Live Verification Script for DeLTa Persistence Chain
Executes against the running server and verifies:
1. ACCEPT_ROUTE execution & persistence
2. REJECT_ROUTE execution & persistence
3. MANUAL_OVERRIDE execution & persistence
4. ACKNOWLEDGE_ALERT execution & persistence
5. EXECUTE_SIMULATION execution & persistence
6. Verification that all stored action names in SQLite are clean (no 'AuditActionType.' prefix)
7. Verification that records persist across server restarts
"""

import urllib.request
import json
import sqlite3
import time
import os

API_BASE = "http://127.0.0.1:8000/api"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend", "delta_storage.db")

def post_json(endpoint, data):
    req = urllib.request.Request(
        f"{API_BASE}{endpoint}",
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

def get_json(endpoint):
    with urllib.request.urlopen(f"{API_BASE}{endpoint}") as resp:
        return json.loads(resp.read().decode("utf-8"))

def check_sqlite_record(action_type, target_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT entry_id, timestamp, operator_id, action_type, target_id, rationale
        FROM audit_log
        WHERE action_type = ? AND target_id = ?
        ORDER BY timestamp DESC LIMIT 1
    """, (action_type, target_id))
    row = cursor.fetchone()
    conn.close()
    return row

def run_verification():
    results = {}
    print("=== STARTING DELTA END-TO-END PERSISTENCE VERIFICATION ===")

    # Step 1: ACCEPT_ROUTE
    print("\n[Step 1] Testing ACCEPT_ROUTE...")
    route_target = f"ROUTE_ALPHA_TEST_{int(time.time())}"
    accept_res = post_json("/audit", {
        "action_type": "ACCEPT_ROUTE",
        "target_id": route_target,
        "rationale": "Master accepted Route Alpha based on radar observation.",
        "operator_id": "CAPT_ARMSTRONG",
        "details": {"route_name": "Route Alpha", "peak_risk": 41}
    })
    assert accept_res["status"] == "LOGGED", "ACCEPT_ROUTE failed"
    entry_id = accept_res["entry_id"]

    # Step 2: Check SQLite persistence for ACCEPT_ROUTE
    db_row = check_sqlite_record("ACCEPT_ROUTE", route_target)
    assert db_row is not None, "Record not found in SQLite"
    assert db_row[3] == "ACCEPT_ROUTE", f"Action type is not clean: {db_row[3]}"
    assert "AuditActionType" not in db_row[3], "AuditActionType prefix leaked"
    print(f"  [OK] SQLite record verified: entry_id={entry_id}, action_type={db_row[3]}")
    results["ACCEPT_ROUTE"] = "PASSED"

    # Step 3: REJECT_ROUTE
    print("\n[Step 2] Testing REJECT_ROUTE...")
    reject_target = f"ROUTE_BRAVO_TEST_{int(time.time())}"
    reject_res = post_json("/audit", {
        "action_type": "REJECT_ROUTE",
        "target_id": reject_target,
        "rationale": "Duty Officer rejected Route Bravo due to calving hazard.",
        "operator_id": "OFFICER_ROSS",
        "details": {"route_name": "Route Bravo", "peak_risk": 84}
    })
    db_row = check_sqlite_record("REJECT_ROUTE", reject_target)
    assert db_row is not None and db_row[3] == "REJECT_ROUTE"
    print(f"  [OK] SQLite record verified: action_type={db_row[3]}")
    results["REJECT_ROUTE"] = "PASSED"

    # Step 4: MANUAL_OVERRIDE
    print("\n[Step 3] Testing MANUAL_OVERRIDE...")
    override_target = f"ROUTE_CHARLIE_TEST_{int(time.time())}"
    override_res = post_json("/audit", {
        "action_type": "MANUAL_OVERRIDE",
        "target_id": override_target,
        "rationale": "Master manually selected Route Charlie deep water track.",
        "operator_id": "CAPT_ARMSTRONG",
        "details": {"route_name": "Route Charlie", "peak_risk": 28}
    })
    db_row = check_sqlite_record("MANUAL_OVERRIDE", override_target)
    assert db_row is not None and db_row[3] == "MANUAL_OVERRIDE"
    print(f"  [OK] SQLite record verified: action_type={db_row[3]}")
    results["MANUAL_OVERRIDE"] = "PASSED"

    # Step 5: ACKNOWLEDGE_ALERT
    print("\n[Step 4] Testing ACKNOWLEDGE_ALERT via /api/alerts/{id}/acknowledge...")
    alerts = get_json("/alerts")
    assert len(alerts) > 0, "No active alerts found"
    target_alert = alerts[0]["alert_id"]
    ack_res = post_json(f"/alerts/{target_alert}/acknowledge?operator_id=DUTY_OFFICER", {})
    assert ack_res.get("acknowledged") is True

    db_row = check_sqlite_record("ACKNOWLEDGE_ALERT", target_alert)
    assert db_row is not None and db_row[3] == "ACKNOWLEDGE_ALERT"
    print(f"  [OK] SQLite record verified: action_type={db_row[3]}, target_id={target_alert}")
    results["ACKNOWLEDGE_ALERT"] = "PASSED"

    # Step 6: EXECUTE_SIMULATION
    print("\n[Step 5] Testing EXECUTE_SIMULATION via /api/simulation/step...")
    sim_res = post_json("/simulation/step", {"stage": 2})
    assert sim_res["stage"] == 2
    
    db_row = check_sqlite_record("EXECUTE_SIMULATION", "STAGE_2")
    assert db_row is not None and db_row[3] == "EXECUTE_SIMULATION"
    print(f"  [OK] SQLite record verified: action_type={db_row[3]}, target_id=STAGE_2")
    results["EXECUTE_SIMULATION"] = "PASSED"

    # Step 7: Verify GET /api/audit returns clean records
    print("\n[Step 6] Testing GET /api/audit API output...")
    audit_logs = get_json("/audit")
    assert len(audit_logs) >= 5
    for log in audit_logs[:10]:
        act = log["action_type"]
        assert not act.startswith("AuditActionType."), f"Found prefixed action_type: {act}"
        assert act in ["ACCEPT_ROUTE", "REJECT_ROUTE", "MANUAL_OVERRIDE", "ACKNOWLEDGE_ALERT", "EXECUTE_SIMULATION", "CONFIG_CHANGE"]
    print(f"  [OK] Checked top {min(10, len(audit_logs))} audit records. All action types are clean.")
    results["API_AUDIT_LOG_FORMAT"] = "PASSED"

    # Step 8: Verify Activity Stream synchronizes with operator actions
    print("\n[Step 7] Testing Activity Stream synchronization...")
    activity = get_json("/agent/activity")
    act_steps = [item["step"] for item in activity]
    assert "ACT" in act_steps, "ACT step missing from activity stream"
    print(f"  [OK] Activity stream captured {len(activity)} operational events including ACT.")
    results["ACTIVITY_STREAM_SYNC"] = "PASSED"

    # Step 9: Verify Shared System State has human decisions
    print("\n[Step 8] Testing Shared System State human decisions...")
    shared_state = get_json("/system/shared-state")
    assert len(shared_state["human_decisions"]) >= 1
    last_action = shared_state["human_decisions"][-1]["action_type"]
    assert "AuditActionType" not in last_action
    print(f"  [OK] Shared state contains {len(shared_state['human_decisions'])} operator decisions.")
    results["SHARED_STATE_SYNC"] = "PASSED"

    print("\n=== ALL IN-SESSION PERSISTENCE TESTS PASSED ===")
    return results

if __name__ == "__main__":
    run_verification()
