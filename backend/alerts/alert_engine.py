"""
Early-Warning Alert Engine
Generates, validates, deduplicates, and manages structured cryosphere and navigational early warnings.
Enforces 7-part operational alert schema: What, Where, When, Evidence, Confidence, Development, Action.
Includes event-driven triggers with 30-minute cooldown and fingerprint deduplication.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import hashlib
from backend.models import (
    AlertPayload, AlertSeverity, DataProvenance, SystemMode,
    RiskScore, RerouteEvaluation, DownstreamHazardAssessment, VesselState
)
from backend.database.db import db

class EarlyWarningAlertEngine:
    def __init__(self):
        self.active_alerts: Dict[str, AlertPayload] = {}
        self.alert_cooldowns: Dict[str, datetime] = {}
        self.cooldown_seconds: float = 1800.0  # 30 minutes
        self._init_default_alerts()

    def _fingerprint(self, alert: AlertPayload) -> str:
        """Create unique signature for deduplication."""
        raw = f"{alert.severity.value}:{alert.where_location_name}:{alert.what[:40]}"
        return hashlib.md5(raw.encode("utf-8")).hexdigest()

    def _init_default_alerts(self):
        """Initial baseline polar warnings."""
        now = datetime.now(timezone.utc)
        a1 = AlertPayload(
            alert_id="ALERT-POLAR-001",
            severity=AlertSeverity.WATCH,
            what="Katabatic Wind Inflow & Sea-Ice Compression Expected in Western Weddell",
            where_lat=-65.80,
            where_lon=-61.20,
            where_location_name="Western Weddell Sea / Larsen C Coastal Flank",
            when_timestamp=now,
            evidence="Atmospheric gradient indicates 35-40 kt southwesterly katabatic gusts developing off the Antarctic Peninsula plateau over the next 12 hours.",
            confidence=0.87,
            uncertainty_pct=13.0,
            provenance=DataProvenance(
                source="Early Warning Alert Engine",
                provider_name="EarlyWarningAlertEngine",
                mode=SystemMode.DEMO,
                is_simulated=True,
                confidence=0.87,
                uncertainty_pct=13.0,
                processing_stage="ALERT_TRIGGER"
            ),
            expected_development="Pack ice will compress against shorefast ice edge, reducing open water leads from 18% to under 6%.",
            recommended_action="Vessels in western leads should maneuver towards central basin open drift before compression intensifies.",
            acknowledged=False
        )
        self.active_alerts[a1.alert_id] = a1
        db.save_alert(a1.model_dump())

    def raise_alert(self, alert: AlertPayload) -> Optional[AlertPayload]:
        """Raise alert with fingerprint deduplication and cooldown check."""
        fp = self._fingerprint(alert)
        now = datetime.now(timezone.utc)

        # Check cooldown
        if fp in self.alert_cooldowns:
            last_time = self.alert_cooldowns[fp]
            if (now - last_time).total_seconds() < self.cooldown_seconds:
                # Still within cooldown window; if identical severity, suppress duplicate
                for existing_id, existing in self.active_alerts.items():
                    if self._fingerprint(existing) == fp and existing.severity == alert.severity:
                        return existing

        self.alert_cooldowns[fp] = now
        self.active_alerts[alert.alert_id] = alert
        db.save_alert(alert.model_dump())
        return alert

    def evaluate_system_events(
        self,
        vessel: VesselState,
        current_risk: RiskScore,
        reroute: Optional[RerouteEvaluation],
        scenario_stage: int = 0
    ) -> List[AlertPayload]:
        """
        Event-driven alert generation based on shared system state:
        - T+6h storm (stage 1): Gale advisory / sea-ice compression alert
        - T+12h calving (stage 2): Critical calving detachment and route safety breach alert
        """
        now = datetime.now(timezone.utc)
        generated = []

        if scenario_stage == 1:
            # Stage 1: T+6h Storm Event
            a_storm = AlertPayload(
                alert_id=f"ALERT-STORM-{int(now.timestamp())}",
                severity=AlertSeverity.WARNING,
                what="Storm Surge & Pressure Drop (968 hPa) Detected Across Corridor",
                where_lat=vessel.position.lat,
                where_lon=vessel.position.lon,
                where_location_name="Northwestern Weddell Sea Marine Corridor",
                when_timestamp=now,
                evidence="Severe gale force gusts (48 kt) driving compressed pack-ice (+14.8%) northeast toward shipping route. Freezing spray risk high.",
                confidence=0.93,
                uncertainty_pct=7.0,
                provenance=DataProvenance(
                    source="DeLTa Event Monitor",
                    provider_name="EarlyWarningAlertEngine",
                    mode=SystemMode.DEMO,
                    is_simulated=True,
                    confidence=0.93,
                    uncertainty_pct=7.0,
                    processing_stage="DYNAMIC_EVENT_TRIGGER",
                    notes="Deterministic evaluation of T+6h storm telemetry"
                ),
                expected_development="Wave heights reaching 4.5m in outer basin within 3 hours. Fast ice edge fracturing.",
                recommended_action="Reduce vessel speed to 8.5 knots. Activate anti-icing countermeasures and ballast down.",
                acknowledged=False
            )
            res = self.raise_alert(a_storm)
            if res:
                generated.append(res)

        elif scenario_stage >= 2:
            # Stage 2: T+12h Major Calving Collapse
            a_calve = AlertPayload(
                alert_id=f"ALERT-CALVE-{int(now.timestamp())}",
                severity=AlertSeverity.CRITICAL,
                what="Major Tabular Iceberg Detachment & Direct Route Obstruction (Larsen C)",
                where_lat=-65.90,
                where_lon=-60.20,
                where_location_name="Larsen C Northern Front (65.9°S, 60.2°W)",
                when_timestamp=now,
                evidence="Sentinel-1 SAR interferometry verifies 820m ice-front detachment. 5 large radar-bright tabular icebergs (BERG-CALVED-NEW-01..05) detected drifting directly across Route Bravo.",
                confidence=0.96,
                uncertainty_pct=4.0,
                provenance=DataProvenance(
                    source="DeLTa Event Monitor",
                    provider_name="EarlyWarningAlertEngine",
                    mode=SystemMode.DEMO,
                    is_simulated=True,
                    confidence=0.96,
                    uncertainty_pct=4.0,
                    processing_stage="DYNAMIC_EVENT_TRIGGER",
                    notes="Deterministic evaluation of T+12h calving telemetry"
                ),
                expected_development="Tabular icebergs drifting NE at 0.8 kt. Secondary growler swarm expanding across 35 km radius.",
                recommended_action="IMMEDIATE ROUTE ABANDONMENT: Divert to Route Alpha (Balanced). Maintain 25 NM buffer from ice front.",
                acknowledged=False
            )
            res = self.raise_alert(a_calve)
            if res:
                generated.append(res)

        return generated

    def get_alerts(self, severity_filter: Optional[str] = None) -> List[AlertPayload]:
        alerts = list(self.active_alerts.values())
        if severity_filter:
            alerts = [a for a in alerts if a.severity.value == severity_filter]
        alerts.sort(key=lambda x: (self._severity_rank(x.severity), x.when_timestamp), reverse=True)
        return alerts

    def acknowledge_alert(self, alert_id: str, operator_id: str = "DUTY_OFFICER") -> Optional[AlertPayload]:
        if alert_id in self.active_alerts:
            a = self.active_alerts[alert_id]
            a.acknowledged = True
            a.acknowledged_by = operator_id
            a.acknowledged_at = datetime.now(timezone.utc)
            db.acknowledge_alert(alert_id, operator_id=operator_id)
            return a
        return None

    def _severity_rank(self, severity: AlertSeverity) -> int:
        ranks = {
            AlertSeverity.CRITICAL: 5,
            AlertSeverity.WARNING: 4,
            AlertSeverity.ADVISORY: 3,
            AlertSeverity.WATCH: 2,
            AlertSeverity.NORMAL: 1
        }
        return ranks.get(severity, 0)

# Global singleton
alert_engine = EarlyWarningAlertEngine()
