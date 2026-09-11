"""
Temporal Change-Detection Engine
Performs multi-temporal observation comparison (T0 -> T1 -> T2 -> Current)
Quantifies front displacement, ice concentration surge, velocity acceleration, and new iceberg generation.
Adheres strictly to deterministic physics formulas:
  Displacement = Δpos
  Velocity = Δpos / Δt
  Acceleration = Δv / Δt
When observations < 2, returns INSUFFICIENT_DATA with 0.0 confidence.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Tuple
import math
from backend.models import TemporalChangeAnalysis, BoundingBox, GeoPoint, DataProvenance, SystemMode

class TemporalChangeEngine:
    def __init__(self):
        pass

    @staticmethod
    def haversine_distance_m(p1: GeoPoint, p2: GeoPoint) -> float:
        """Calculate great-circle distance between two points on the Earth surface in meters."""
        R = 6371000.0  # Earth radius in meters
        phi1 = math.radians(p1.lat)
        phi2 = math.radians(p2.lat)
        delta_phi = math.radians(p2.lat - p1.lat)
        delta_lambda = math.radians(p2.lon - p1.lon)

        a = (math.sin(delta_phi / 2.0) ** 2 +
             math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2))
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return R * c

    def compute_kinematics(
        self,
        positions_with_timestamps: List[Tuple[GeoPoint, datetime]]
    ) -> Dict[str, Any]:
        """
        Deterministic physics calculation of displacement, velocity, and acceleration.
        If observations < 2, returns INSUFFICIENT_DATA with confidence 0.0.
        """
        if len(positions_with_timestamps) < 2:
            return {
                "status": "INSUFFICIENT_DATA",
                "displacement_m": 0.0,
                "velocity_m_per_day": 0.0,
                "acceleration_m_per_day2": 0.0,
                "confidence": 0.0,
                "uncertainty_pct": 100.0
            }

        # Sort chronologically
        sorted_points = sorted(positions_with_timestamps, key=lambda x: x[1])
        p0, t0 = sorted_points[0]
        p1, t1 = sorted_points[1]

        dt_sec_1 = (t1 - t0).total_seconds()
        if dt_sec_1 <= 0:
            dt_sec_1 = 1.0
        dt_days_1 = dt_sec_1 / 86400.0

        disp_1 = self.haversine_distance_m(p0, p1)
        v1 = disp_1 / dt_days_1

        if len(sorted_points) >= 3:
            p2, t2 = sorted_points[2]
            dt_sec_2 = (t2 - t1).total_seconds()
            if dt_sec_2 <= 0:
                dt_sec_2 = 1.0
            dt_days_2 = dt_sec_2 / 86400.0
            disp_2 = self.haversine_distance_m(p1, p2)
            v2 = disp_2 / dt_days_2
            total_disp = self.haversine_distance_m(p0, p2)
            accel = (v2 - v1) / ((dt_days_1 + dt_days_2) / 2.0)
            confidence = 0.95
        else:
            total_disp = disp_1
            accel = 0.0
            confidence = 0.88

        return {
            "status": "COMPLETED",
            "displacement_m": round(total_disp, 2),
            "velocity_m_per_day": round(v1, 3),
            "acceleration_m_per_day2": round(accel, 4),
            "confidence": confidence,
            "uncertainty_pct": round((1.0 - confidence) * 100.0, 1)
        }

    def compare_observations(
        self,
        region_id: str,
        t0_time: datetime,
        t1_time: datetime,
        scenario_stage: int = 0
    ) -> TemporalChangeAnalysis:
        """
        Compare baseline observation (T0) with newest observation (T1).
        In scenario_stage >= 1: models a major sudden ice-shelf calving event (Larsen C / Brunt front fracture).
        Propagates explicit uncertainty metrics and deterministic deltas.
        """
        delta_seconds = abs((t1_time - t0_time).total_seconds())
        delta_days = max(0.1, round(delta_seconds / 86400.0, 2))

        if scenario_stage == 0:
            # Baseline steady state
            ice_conc_delta = 4.2
            iceberg_delta = 1
            front_disp = -45.0  # -45m slow steady ablation
            velocity_change = 2.1 # +2.1%
            accel_detected = False
            confidence = 0.94
            summary = (
                f"Cryosphere observation across {delta_days} days indicates baseline equilibrium. "
                f"Sea ice concentration increased marginally (+{ice_conc_delta}%), "
                f"front position displaced by {front_disp}m. No anomalous calving detected. "
                f"[DEMO Scenario Baseline | Confidence: {confidence*100:.1f}%]"
            )
        elif scenario_stage == 1:
            # T+6h Storm Surge & Pressure Drop
            ice_conc_delta = 18.5
            iceberg_delta = 3
            front_disp = -320.0
            velocity_change = 24.5
            accel_detected = True
            confidence = 0.93
            summary = (
                f"Storm event (T+6h): Catabatic gales driving pack ice drift (+{ice_conc_delta}%) into navigation channel. "
                f"Glacier terminus displacement -{abs(front_disp)}m with initial fracture widening. "
                f"[DEMO Scenario T+6h Storm | Confidence: {confidence*100:.1f}%]"
            )
        else:
            # Stage 2+ (T+12h): Dynamic Calving & Pack Ice Inflow Event!
            ice_conc_delta = 25.5  # Surge from 42% to 67.5%
            iceberg_delta = 5     # 5 new large icebergs calved into channel
            front_disp = -820.0   # 820m catastrophic ice-front collapse
            velocity_change = 48.6 # +48.6% surge acceleration in glacier movement
            accel_detected = True
            confidence = 0.96
            summary = (
                f"CRITICAL CRYOSPHERE DISCOVERY (T+12h): Temporal change analysis across {delta_days} days detects "
                f"catastrophic ice-front calving (-{abs(front_disp)}m detachment) and sudden pack-ice surge (+{ice_conc_delta}%). "
                f"Glacier motion has accelerated by +{velocity_change}%. 5 new large radar bright-targets (icebergs) "
                f"are now drifting northeast directly crossing navigation tracks. "
                f"[DEMO Scenario T+12h Calving Event | Confidence: {confidence*100:.1f}%]"
            )

        return TemporalChangeAnalysis(
            glacier_or_region_id=region_id,
            t0_timestamp=t0_time,
            t1_timestamp=t1_time,
            delta_days=delta_days,
            sea_ice_concentration_delta_pct=ice_conc_delta,
            iceberg_count_delta=iceberg_delta,
            front_displacement_m=front_disp,
            velocity_change_pct=velocity_change,
            acceleration_detected=accel_detected,
            summary=summary,
            confidence=confidence
        )
