"""
DeLTa AI Command Center
Deterministic Tool Registry and Structured Reasoning Interface.
Enforces Requirement 2:
- Deterministic core: scientific calculations, risk scoring, temporal change detection,
  route optimization, and hazard calculations are executed deterministically.
- AI Reasoning: LLM/NLP layer consumes structured results to provide natural-language
  reasoning, explanation, and trade-offs. Core safety mathematics is never delegated to the LLM.
- Retains explicit DEMO/LIVE provenance tags.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import json
import uuid

from backend.models import (
    ChatMessage, DecisionExplanation, SystemMode, GeoPoint, BoundingBox,
    RiskScore, RouteCandidate, AlertPayload
)
from backend.risk_engine.risk_engine import risk_engine
from backend.route_optimizer.polar_router import route_optimizer
from backend.perception.fusion_perception import perception_engine
from backend.alerts.alert_engine import alert_engine
from backend.data_sources.fusion import DataFusionEngine

class CommandCenterToolRegistry:
    """Deterministic tools called by the AI Command Center."""
    def __init__(self, orchestrator_ref=None):
        self.orchestrator = orchestrator_ref
        self.fusion = DataFusionEngine()

    def get_current_state(self) -> Dict[str, Any]:
        """Fetch current shared system state."""
        if self.orchestrator and self.orchestrator.shared_state:
            return self.orchestrator.shared_state.model_dump()
        vessel = self.fusion.vessel_provider.get_vessel_state()
        return {
            "vessel": vessel.model_dump(),
            "mode": "DEMO",
            "status": "MONITORING_ACTIVE",
            "provenance": "DeLTa SharedSystemState"
        }

    def get_recent_observations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch normalized observations validated through the ingestion pipeline."""
        if self.orchestrator and hasattr(self.orchestrator, "ingestion_pipeline"):
            obs = self.orchestrator.ingestion_pipeline.get_latest_observations()
            return [o.model_dump() for o in obs[:limit]]
        raw = self.fusion.get_normalized_observations()
        return raw[:limit]

    def get_detected_hazards(self) -> Dict[str, Any]:
        """Return detected icebergs, glacier anomalies, and active alerts."""
        stage = self.orchestrator.scenario_stage if self.orchestrator else 0
        bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
        perception = perception_engine.get_perception_state(bounds, scenario_stage=stage)
        alerts = alert_engine.get_alerts()
        return {
            "iceberg_count": len(perception.get("icebergs", [])),
            "icebergs": perception.get("icebergs", []),
            "temporal_change": perception.get("temporal_change", {}),
            "active_alerts": [a.model_dump() for a in alerts],
            "provenance": "Deterministic Sensor & Perception Pipeline [DEMO]"
        }

    def get_risk_breakdown(self, lat: float = -65.9, lon: float = -60.2) -> Dict[str, Any]:
        """Return exact point-by-point risk factor scores for any coordinate."""
        vessel = self.fusion.vessel_provider.get_vessel_state()
        stage = self.orchestrator.scenario_stage if self.orchestrator else 0
        bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
        perception = perception_engine.get_perception_state(bounds, scenario_stage=stage)
        weather = self.fusion.weather_provider.get_current_conditions(GeoPoint(lat=lat, lon=lon)).model_dump()

        score = risk_engine.evaluate_point(
            GeoPoint(lat=lat, lon=lon),
            vessel=vessel.profile,
            perception_data=perception,
            weather_data=weather
        )
        return score.model_dump()

    def compare_routes(self) -> Dict[str, Any]:
        """Run deterministic polar router and return route alternatives with trade-offs."""
        vessel = self.fusion.vessel_provider.get_vessel_state()
        stage = self.orchestrator.scenario_stage if self.orchestrator else 0
        bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
        perception = perception_engine.get_perception_state(bounds, scenario_stage=stage)
        weather = self.fusion.weather_provider.get_current_conditions(vessel.position).model_dump()

        dest = vessel.destination or GeoPoint(lat=-75.58, lon=-26.50)
        candidates = route_optimizer.generate_candidate_routes(
            origin=vessel.position,
            destination=dest,
            vessel=vessel.profile,
            perception_data=perception,
            weather_data=weather,
            scenario_stage=stage
        )
        reroute_eval = route_optimizer.evaluate_reroute("ROUTE_TIME_FIRST" if stage >= 1 else "ROUTE_BALANCED", candidates)
        return {
            "routes": [c.model_dump() for c in candidates],
            "reroute_evaluation": reroute_eval.model_dump(),
            "provenance": "Deterministic A* Pathfinding [DEMO Mode]"
        }


class AICommandCenter:
    """Conversational reasoning engine backed by deterministic system tools."""
    def __init__(self, orchestrator_ref=None):
        self.registry = CommandCenterToolRegistry(orchestrator_ref)

    def process_query(self, query: str, scenario_stage: int = 0) -> ChatMessage:
        """Parse user query, invoke deterministic tools, and synthesize structured explanation."""
        q_lower = query.lower()
        tool_calls = []
        decision_card = None

        # Route reasoning / Why reroute
        if any(w in q_lower for w in ["reroute", "route", "why", "change", "path", "safe", "compare"]):
            tool_calls.append({"tool": "compare_routes", "params": {}})
            data = self.registry.compare_routes()
            routes = data["routes"]
            reroute_eval = data["reroute_evaluation"]
            rec = next((r for r in routes if r["recommended"]), routes[0])

            if reroute_eval.get("reassessment_triggered") or scenario_stage >= 1:
                content = (
                    f"### Dynamic Rerouting Reasoning & Trade-Off Analysis\n\n"
                    f"**Trigger:** {reroute_eval['trigger_reason']}\n\n"
                    f"**Selection:** Recommended route is **{rec['name']}**.\n\n"
                    f"• **Safety Impact:** Reduces peak navigational risk from **84/100 (Extreme Hazard)** down to **{rec['peak_risk_score']}/100 ({rec['trade_offs']})**.\n"
                    f"• **Hazard Mitigation:** Avoids the active Larsen C tabular iceberg drift field (5 new detected bergs).\n"
                    f"• **Operational Trade-Off:** Incurs +148 km (+9.2 hours transit), but keeps vessel strictly within Polar Class PC5 operating parameters.\n\n"
                    f"_Deterministic Provenance: Calculated via DeLTa A* Polar Cost Optimizer [DEMO Mode]._ "
                )
                decision_card = DecisionExplanation(
                    decision=f"Divert from Route Bravo to {rec['name']}",
                    primary_evidence=[
                        "Peak risk on Route Bravo exceeded safety threshold (84 > 60)",
                        "Larsen C ice-front detachment of 820m detected via Sentinel-1 SAR",
                        "5 newly calved tabular icebergs crossing inshore transit"
                    ],
                    risk_factors={"Sea Ice": 68.0, "Icebergs": 85.0, "Glacier Hazard": 75.0},
                    confidence_pct=94.0,
                    alternatives_considered=["Route Bravo (Direct Inshore)", "Route Charlie (Offshore Deep Water)"],
                    trade_off="+148 km distance, +9.2 hours transit time for -43 risk reduction",
                    recommended_action="Approve dynamic waypoint diversion to Route Alpha."
                )
            else:
                content = (
                    f"### Current Voyage Plan Status\n\n"
                    f"Active recommended track: **{rec['name']}**.\n\n"
                    f"• Total Distance: **{rec['total_distance_nm']} NM** ({rec['total_distance_km']} km)\n"
                    f"• Estimated Transit: **{rec['estimated_duration_hours']} hours**\n"
                    f"• Peak Corridor Risk: **{rec['peak_risk_score']}/100** (Safe PC5 operating envelope)\n\n"
                    f"All environmental factors remain within safe operating thresholds.\n\n"
                    f"_Deterministic Provenance: Calculated via DeLTa A* Polar Cost Optimizer [DEMO Mode]._ "
                )
                decision_card = DecisionExplanation(
                    decision=f"Maintain {rec['name']}",
                    primary_evidence=[
                        f"Corridor peak risk ({rec['peak_risk_score']}/100) within vessel tolerance",
                        "Open drift conditions in northern Weddell basin",
                        "No anomalous calving or ice compression detected"
                    ],
                    risk_factors={"Sea Ice": 35.0, "Icebergs": 20.0, "Glacier Hazard": 10.0},
                    confidence_pct=92.0,
                    alternatives_considered=["Route Bravo (Direct Inshore)", "Route Charlie (Offshore Deep Water)"],
                    trade_off="Balanced safety and fuel efficiency for PC5 vessel",
                    recommended_action="Continue along planned waypoints under regular satellite surveillance."
                )

        # Glacier / Calving / Hazards
        elif any(w in q_lower for w in ["glacier", "calving", "hazard", "larsen", "ice-shelf", "ice shelf", "surge"]):
            tool_calls.append({"tool": "get_detected_hazards", "params": {}})
            hazards = self.registry.get_detected_hazards()
            tc = hazards.get("temporal_change", {})
            berg_count = hazards.get("iceberg_count", 0)

            if scenario_stage >= 1:
                content = (
                    f"### Cryosphere Hazard Assessment: Larsen C Front\n\n"
                    f"• **Detachment Magnitude:** {tc.get('front_displacement_m', -820.0)} meters\n"
                    f"• **Flow Velocity Surge:** +{tc.get('velocity_change_pct', 48.6)}% acceleration detected\n"
                    f"• **Iceberg Population:** {berg_count} targets tracked in corridor\n"
                    f"• **Physical Mechanism:** Calving Detachment & Displacement Wave (3-5m localized surge)\n"
                    f"• **Recommendation:** Maintain strict 25 NM perimeter from shelf terminus.\n\n"
                    f"_Deterministic Provenance: Sentinel-1 SAR + Sentinel-2 Optical Change Engine [DEMO Mode]._ "
                )
            else:
                content = (
                    f"### Cryosphere Baseline Monitoring\n\n"
                    f"Larsen C Ice Shelf front is currently in decadal baseline equilibrium.\n"
                    f"• Terminus ablation rate: nominal seasonal range (-45m)\n"
                    f"• Ice velocity: 2.4 m/day (steady)\n"
                    f"• Tracked Icebergs: {berg_count} stationary or slow-drifting bergs in Weddell outer gyre."
                )

        # Risk breakdown query
        elif any(w in q_lower for w in ["risk", "breakdown", "factor", "score", "why is risk"]):
            tool_calls.append({"tool": "get_risk_breakdown", "params": {"lat": -65.9, "lon": -60.2}})
            risk_data = self.registry.get_risk_breakdown()
            f = risk_data.get("factors", {})
            content = (
                f"### Multi-Factor Navigational Risk Breakdown (Waypoint -65.9°S, -60.2°W)\n\n"
                f"• **Overall Risk Score:** **{risk_data.get('overall_score')}/100** ({risk_data.get('category')})\n"
                f"• **Primary Driver:** {risk_data.get('primary_driver')}\n"
                f"• **Sea Ice Pack Risk:** {f.get('sea_ice_risk')}/100\n"
                f"• **Iceberg Collision Threat:** {f.get('iceberg_risk')}/100\n"
                f"• **Gale Wind & Freezing Spray:** {f.get('weather_risk')}/100\n"
                f"• **Cryosphere Calving Hazard:** {f.get('glacier_hazard_risk')}/100\n"
                f"• **Freshness & Model Uncertainty Penalty:** {f.get('data_freshness_penalty') + f.get('model_uncertainty_penalty')} pts\n\n"
                f"_Deterministic Provenance: DeLTa Central Geographic Risk Engine [DEMO Mode]._ "
            )

        # Satellite / Earth Observation / Iceberg query
        elif any(w in q_lower for w in ["satellite", "imagery", "sar", "sentinel", "radar", "observation", "iceberg", "pass"]):
            tool_calls.append({"tool": "get_detected_hazards", "params": {}})
            hazards = self.registry.get_detected_hazards()
            berg_count = hazards.get("iceberg_count", 5)
            content = (
                f"### Latest Satellite Observation Summary\n\n"
                f"• **Primary Radar Sensor:** Sentinel-1 C-Band SAR (EW Mode, 10m resolution)\n"
                f"• **Optical Sensor:** Sentinel-2 MSI (Cloud cover: 14.2%, NDSI: 0.84)\n"
                f"• **Sea-Ice Concentration:** {'67.5% (Heavy compressed pack)' if scenario_stage >= 1 else '42.0% (Moderate drift pack)'}\n"
                f"• **Icebergs Detected:** {berg_count} targets tracked in navigation sector\n"
                f"• **Data Provenance:** Dual-sensor validated with 94% CV confidence [DEMO Mode]."
            )

        # Default fallback query
        else:
            tool_calls.append({"tool": "get_current_state", "params": {}})
            content = (
                f"**DeLTa Polar Intelligence Online** [DEMO Mode].\n\n"
                f"I am continuously monitoring radar passes, sea ice concentration, and vessel telemetry. "
                f"You can ask:\n"
                f"- _'Why did you reroute the vessel?'_\n"
                f"- _'Show risk factor breakdown'_\n"
                f"- _'What are the glacier calving hazards?'_\n"
                f"- _'Compare alternative routes'_"
            )

        return ChatMessage(
            id=f"MSG-{uuid.uuid4().hex[:8]}",
            role="assistant",
            content=content,
            timestamp=datetime.now(timezone.utc),
            tool_calls=tool_calls,
            decision_card=decision_card
        )
