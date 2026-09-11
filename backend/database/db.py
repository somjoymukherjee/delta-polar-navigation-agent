"""
DeLTa Database Manager
Lightweight, thread-safe persistent store for observations, satellite passes,
routes, cryosphere hazards, alerts, and audit logs.
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "delta_storage.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # Satellite Images Catalog
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS satellite_images (
            image_id TEXT PRIMARY KEY,
            source TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            acquisition_time TEXT NOT NULL,
            bounds_json TEXT NOT NULL,
            cloud_cover_pct REAL,
            resolution_m REAL,
            quality_status TEXT,
            is_demo INTEGER DEFAULT 0,
            preview_url TEXT,
            metadata_json TEXT
        )
        """)

        # Environmental & Ocean Observations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS observations (
            id TEXT PRIMARY KEY,
            obs_type TEXT NOT NULL, -- weather, ocean, ice, iceberg, glacier
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            timestamp TEXT NOT NULL,
            source TEXT NOT NULL,
            quality_status TEXT NOT NULL,
            confidence REAL NOT NULL,
            data_json TEXT NOT NULL
        )
        """)

        # Icebergs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS icebergs (
            id TEXT PRIMARY KEY,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            length_m REAL,
            width_m REAL,
            area_sqm REAL,
            drift_speed_knots REAL,
            drift_direction_deg REAL,
            confidence REAL,
            sensor_type TEXT,
            timestamp TEXT NOT NULL
        )
        """)

        # Sea Ice Observations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sea_ice (
            grid_id TEXT PRIMARY KEY,
            bounds_json TEXT NOT NULL,
            center_lat REAL,
            center_lon REAL,
            concentration_pct REAL NOT NULL,
            stage TEXT,
            thickness_cm REAL,
            timestamp TEXT NOT NULL
        )
        """)

        # Glaciers & Ice Shelves
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS glaciers (
            glacier_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            front_lat REAL NOT NULL,
            front_lon REAL NOT NULL,
            velocity_m_per_day REAL,
            acceleration_m_per_day2 REAL,
            retreat_distance_m REAL,
            calving_activity TEXT,
            trend TEXT,
            confidence REAL,
            timestamp TEXT NOT NULL,
            details_json TEXT
        )
        """)

        # Routes
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS routes (
            route_id TEXT PRIMARY KEY,
            profile TEXT NOT NULL,
            name TEXT NOT NULL,
            waypoints_json TEXT NOT NULL,
            total_distance_km REAL NOT NULL,
            estimated_duration_hours REAL NOT NULL,
            average_risk_score REAL NOT NULL,
            peak_risk_score REAL NOT NULL,
            fuel_estimate_tons REAL NOT NULL,
            major_hazards_json TEXT,
            trade_offs TEXT,
            recommended INTEGER DEFAULT 0,
            generated_at TEXT NOT NULL
        )
        """)

        # Alerts
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            severity TEXT NOT NULL,
            what TEXT NOT NULL,
            where_lat REAL NOT NULL,
            where_lon REAL NOT NULL,
            where_location_name TEXT NOT NULL,
            when_timestamp TEXT NOT NULL,
            evidence TEXT NOT NULL,
            confidence REAL NOT NULL,
            expected_development TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0,
            acknowledged_by TEXT,
            acknowledged_at TEXT
        )
        """)

        # Audit Log
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            entry_id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            operator_id TEXT NOT NULL,
            action_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            details_json TEXT NOT NULL,
            rationale TEXT NOT NULL
        )
        """)

        # Agent Memory & Key-Value State
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_memory (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """)

        conn.commit()
        conn.close()

    # --- Satellite Methods ---
    def save_satellite_image(self, data: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO satellite_images 
        (image_id, source, sensor_type, acquisition_time, bounds_json, cloud_cover_pct, resolution_m, quality_status, is_demo, preview_url, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["image_id"], data["source"], data["sensor_type"], data["acquisition_time"],
            json.dumps(data["bounds"]), data.get("cloud_cover_pct", 0.0), data.get("resolution_m", 10.0),
            data.get("quality_status", "GOOD"), 1 if data.get("is_demo", False) else 0,
            data.get("preview_url", ""), json.dumps(data.get("metadata", {}))
        ))
        conn.commit()
        conn.close()

    def get_satellite_images(self, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM satellite_images ORDER BY acquisition_time DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["bounds"] = json.loads(d["bounds_json"])
            d["metadata"] = json.loads(d["metadata_json"]) if d["metadata_json"] else {}
            d["is_demo"] = bool(d["is_demo"])
            result.append(d)
        conn.close()
        return result

    # --- Iceberg Methods ---
    def save_icebergs(self, icebergs: List[Dict[str, Any]]):
        conn = self._get_connection()
        cursor = conn.cursor()
        for b in icebergs:
            cursor.execute("""
            INSERT OR REPLACE INTO icebergs 
            (id, lat, lon, length_m, width_m, area_sqm, drift_speed_knots, drift_direction_deg, confidence, sensor_type, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                b["id"], b["lat"], b["lon"], b.get("length_m", 100), b.get("width_m", 80),
                b.get("area_sqm", 8000), b.get("drift_speed_knots", 0.5), b.get("drift_direction_deg", 45),
                b.get("confidence", 0.9), b.get("sensor_type", "Sentinel-1"), b["timestamp"]
            ))
        conn.commit()
        conn.close()

    def get_icebergs(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM icebergs ORDER BY timestamp DESC")
        rows = [dict(r) for r in cursor.fetchall()]
        conn.close()
        return rows

    # --- Glacier Methods ---
    def save_glacier(self, glacier: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO glaciers
        (glacier_id, name, front_lat, front_lon, velocity_m_per_day, acceleration_m_per_day2, retreat_distance_m, calving_activity, trend, confidence, timestamp, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            glacier["glacier_id"], glacier["name"], glacier["front_lat"], glacier["front_lon"],
            glacier.get("velocity_m_per_day", 0.0), glacier.get("acceleration_m_per_day2", 0.0),
            glacier.get("retreat_distance_m", 0.0), glacier.get("calving_activity", "MODERATE"),
            glacier.get("trend", "STABLE"), glacier.get("confidence", 0.9), glacier["timestamp"],
            json.dumps(glacier.get("details", {}))
        ))
        conn.commit()
        conn.close()

    def get_glaciers(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM glaciers")
        rows = cursor.fetchall()
        res = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d["details_json"]) if d["details_json"] else {}
            res.append(d)
        conn.close()
        return res

    # --- Route Methods ---
    def save_route(self, route: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        gen_at = route["generated_at"].isoformat() if hasattr(route["generated_at"], "isoformat") else str(route["generated_at"])
        cursor.execute("""
        INSERT OR REPLACE INTO routes
        (route_id, profile, name, waypoints_json, total_distance_km, estimated_duration_hours, average_risk_score, peak_risk_score, fuel_estimate_tons, major_hazards_json, trade_offs, recommended, generated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            route["route_id"], str(route["profile"]), route["name"], json.dumps(route["waypoints"]),
            route["total_distance_km"], route["estimated_duration_hours"], route["average_risk_score"],
            route["peak_risk_score"], route["fuel_estimate_tons"], json.dumps(route.get("major_hazards", [])),
            route.get("trade_offs", ""), 1 if route.get("recommended", False) else 0, gen_at
        ))
        conn.commit()
        conn.close()

    def get_routes(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM routes ORDER BY generated_at DESC")
        rows = cursor.fetchall()
        res = []
        for r in rows:
            d = dict(r)
            d["waypoints"] = json.loads(d["waypoints_json"])
            d["major_hazards"] = json.loads(d["major_hazards_json"]) if d["major_hazards_json"] else []
            d["recommended"] = bool(d["recommended"])
            res.append(d)
        conn.close()
        return res

    # --- Alert Methods ---
    def save_alert(self, alert: Dict[str, Any]):
        conn = self._get_connection()
        cursor = conn.cursor()
        when_ts = alert["when_timestamp"].isoformat() if hasattr(alert["when_timestamp"], "isoformat") else str(alert["when_timestamp"])
        cursor.execute("""
        INSERT OR REPLACE INTO alerts
        (alert_id, severity, what, where_lat, where_lon, where_location_name, when_timestamp, evidence, confidence, expected_development, recommended_action, acknowledged, acknowledged_by, acknowledged_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert["alert_id"], str(alert["severity"]), alert["what"], alert["where_lat"], alert["where_lon"],
            alert["where_location_name"], when_ts, alert["evidence"], alert["confidence"],
            alert["expected_development"], alert["recommended_action"], 1 if alert.get("acknowledged", False) else 0,
            alert.get("acknowledged_by"), alert.get("acknowledged_at")
        ))
        conn.commit()
        conn.close()

    def get_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM alerts ORDER BY when_timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        res = []
        for r in rows:
            d = dict(r)
            d["acknowledged"] = bool(d["acknowledged"])
            res.append(d)
        conn.close()
        return res

    def acknowledge_alert(self, alert_id: str, operator_id: str = "DUTY_OFFICER"):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE alerts SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
        WHERE alert_id = ?
        """, (operator_id, datetime.now(timezone.utc).isoformat(), alert_id))
        conn.commit()
        conn.close()

    # --- Audit Log Methods ---
    def save_audit_log(self, entry: Dict[str, Any]):
        act_raw = entry["action_type"]
        act_val = act_raw.value if hasattr(act_raw, "value") else str(act_raw)
        if act_val.startswith("AuditActionType."):
            act_val = act_val.replace("AuditActionType.", "")
        self.log_audit_action(
            entry_id=entry["entry_id"],
            action_type=act_val,
            target_id=entry["target_id"],
            details=entry.get("details", {}),
            rationale=entry.get("rationale", ""),
            operator_id=entry.get("operator_id", "DUTY_OFFICER")
        )

    def log_audit_action(self, entry_id: str, action_type: Any, target_id: str, details: Dict[str, Any], rationale: str, operator_id: str = "DUTY_OFFICER"):
        conn = self._get_connection()
        cursor = conn.cursor()
        act_val = action_type.value if hasattr(action_type, "value") else str(action_type)
        if act_val.startswith("AuditActionType."):
            act_val = act_val.replace("AuditActionType.", "")
        cursor.execute("""
        INSERT OR REPLACE INTO audit_log (entry_id, timestamp, operator_id, action_type, target_id, details_json, rationale)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id, datetime.now(timezone.utc).isoformat(), operator_id, act_val, target_id,
            json.dumps(details), rationale
        ))
        conn.commit()
        conn.close()

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        res = []
        for r in rows:
            d = dict(r)
            d["details"] = json.loads(d["details_json"]) if d["details_json"] else {}
            if "action_type" in d and str(d["action_type"]).startswith("AuditActionType."):
                d["action_type"] = str(d["action_type"]).replace("AuditActionType.", "")
            res.append(d)
        conn.close()
        return res

    # --- Agent Memory Methods ---
    def set_memory(self, key: str, value: Any):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO agent_memory (key, value_json, updated_at)
        VALUES (?, ?, ?)
        """, (key, json.dumps(value), datetime.now(timezone.utc).isoformat()))
        conn.commit()
        conn.close()

    def get_memory(self, key: str, default: Any = None) -> Any:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value_json FROM agent_memory WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return json.loads(row["value_json"])
        return default

# Global Singleton
db = DatabaseManager()
