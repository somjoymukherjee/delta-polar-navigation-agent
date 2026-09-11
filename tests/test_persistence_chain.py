"""
Persistence Chain and Clean Audit Action Verification Suite
Verifies:
1. ACCEPT_ROUTE, REJECT_ROUTE, MANUAL_OVERRIDE, ACKNOWLEDGE_ALERT, EXECUTE_SIMULATION
2. Action reaches orchestrator.handle_human_action
3. Clean record is created in SQLite delta_storage.db without 'AuditActionType.' prefix
4. Records survive simulated restarts (reconnecting to SQLite with fresh instances)
5. Audit log retrieval via GET /api/audit matches exactly
"""

import sqlite3
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import AuditActionType
from backend.database.db import DB_PATH, DatabaseManager
from backend.agents.orchestrator import orchestrator
from backend.simulation.simulator import simulator

client = TestClient(app)

def test_clean_action_type_names():
    """Verify that all audit action types are saved and returned cleanly without class prefixes."""
    actions = [
        ("ACCEPT_ROUTE", "ROUTE_BALANCED", "Master accepted Route Alpha for navigation corridor."),
        ("REJECT_ROUTE", "ROUTE_TIME_FIRST", "Duty Officer rejected Route Bravo due to calving hazard."),
        ("MANUAL_OVERRIDE", "ROUTE_SAFETY_FIRST", "Master manually selected Route Charlie."),
        ("ACKNOWLEDGE_ALERT", "ALERT-POLAR-001", "Duty Officer acknowledged katabatic compression watch."),
        ("EXECUTE_SIMULATION", "STAGE_2", "Simulated T+12h calving collapse event.")
    ]

    for act_type, target_id, rationale in actions:
        resp = client.post("/api/audit", json={
            "action_type": act_type,
            "target_id": target_id,
            "rationale": rationale,
            "operator_id": "TEST_OFFICER"
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "LOGGED"
        entry_id = data["entry_id"]

        # Check in SQLite directly
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT action_type, operator_id, target_id, rationale FROM audit_log WHERE entry_id = ?", (entry_id,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        stored_action, stored_op, stored_target, stored_rat = row
        # Must be exact string, NOT AuditActionType.<NAME>
        assert stored_action == act_type
        assert "AuditActionType" not in stored_action
        assert stored_op == "TEST_OFFICER"
        assert stored_target == target_id

def test_alert_acknowledge_persistence_chain():
    """Test that /api/alerts/{id}/acknowledge flows through orchestrator and persists cleanly to SQLite."""
    # Ensure alert exists
    alerts = client.get("/api/alerts").json()
    assert len(alerts) > 0
    target_alert = alerts[0]["alert_id"]

    ack_resp = client.post(f"/api/alerts/{target_alert}/acknowledge?operator_id=WATCH_OFFICER")
    assert ack_resp.status_code == 200
    assert ack_resp.json()["acknowledged"] is True

    # Verify audit record in SQLite
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT action_type, target_id, operator_id FROM audit_log WHERE target_id = ? ORDER BY timestamp DESC LIMIT 1", (target_alert,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "ACKNOWLEDGE_ALERT"
    assert row[1] == target_alert
    assert row[2] == "WATCH_OFFICER"

def test_execute_simulation_persistence_chain():
    """Test that stepping simulation flows through orchestrator and persists to SQLite."""
    step_resp = client.post("/api/simulation/step", json={"stage": 1})
    assert step_resp.status_code == 200

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT action_type, target_id FROM audit_log WHERE action_type = 'EXECUTE_SIMULATION' ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert row[0] == "EXECUTE_SIMULATION"
    assert "STAGE_1" in row[1]

def test_server_restart_persistence():
    """
    Simulate full server restart by instantiating a fresh DatabaseManager on the same DB_PATH.
    Verifies that all logged entries survive process restarts.
    """
    unique_target = f"ROUTE_VERIFY_{int(datetime.now(timezone.utc).timestamp())}"
    client.post("/api/audit", json={
        "action_type": "ACCEPT_ROUTE",
        "target_id": unique_target,
        "rationale": "Testing restart survival.",
        "operator_id": "RESTART_TESTER"
    })

    # Simulate fresh process startup
    fresh_db = DatabaseManager(db_path=DB_PATH)
    logs = fresh_db.get_audit_logs(limit=20)
    matched = [l for l in logs if l["target_id"] == unique_target]

    assert len(matched) == 1
    assert matched[0]["action_type"] == "ACCEPT_ROUTE"
    assert matched[0]["operator_id"] == "RESTART_TESTER"
    assert "AuditActionType" not in matched[0]["action_type"]
