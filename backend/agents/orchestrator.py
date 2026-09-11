"""
Central AI Orchestrator (DeLTa Master Agent)
Executes the continuous autonomous agent loop:
OBSERVE -> PERCEIVE -> COMPARE -> REASON -> ASSESS RISK -> PLAN -> ACT -> MONITOR

Maintains single source of truth (SharedSystemState), logs AgentCycleRecords,
coordinates tool execution via AICommandCenter, records Human-in-the-Loop audit entries,
and drives the deterministic Golden End-to-End Scenario:
T+0 Baseline -> T+6h Storm -> T+12h Calving Event -> Reroute -> Alert -> Human Decision -> Audit.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import json
import uuid
import time

from backend.models import (
    AgentStep, AgentLoopState, SystemMode, DecisionExplanation,
    ChatMessage, GeoPoint, BoundingBox, RouteCandidate, AlertSeverity, AlertPayload,
    SharedSystemState, UnifiedAgentState, AgentActivityLogItem, AgentCycleRecord,
    RiskDeltaBreakdown, RiskFactorBreakdown, AuditActionType, AuditLogEntry,
    DataProvenance, VesselState
)
from backend.ingestion.pipeline import IngestionPipeline
from backend.perception.fusion_perception import perception_engine
from backend.risk_engine.risk_engine import risk_engine
from backend.route_optimizer.polar_router import route_optimizer
from backend.agents.navigation_agent import navigation_agent
from backend.agents.hazard_agent import hazard_agent
from backend.alerts.alert_engine import alert_engine
from backend.agents.command_center import AICommandCenter
from backend.database.db import db

class AIOrchestrator:
    def __init__(self):
        self.scenario_stage: int = 0
        self.system_mode: SystemMode = SystemMode.DEMO
        self.current_step: AgentStep = AgentStep.MONITOR
        self.last_cycle_time: datetime = datetime.now(timezone.utc)
        self.cycle_counter: int = 0

        self.chat_history: List[ChatMessage] = []
        self.activity_stream: List[AgentActivityLogItem] = []
        self.cycle_records: List[AgentCycleRecord] = []
        self.human_actions: List[Dict[str, Any]] = []

        self.ingestion_pipeline = IngestionPipeline(mode=self.system_mode)
        self.shared_state: Optional[SharedSystemState] = None
        self.unified_state: Optional[SharedSystemState] = None
        self.command_center = AICommandCenter(orchestrator_ref=self)

        self._init_chat_greeting()
        self._init_activity_stream()
        # Initialize initial baseline shared state
        self.run_autonomous_cycle(force_stage=0)

    def _init_chat_greeting(self):
        self.chat_history.append(ChatMessage(
            id="MSG-SYS-INIT",
            role="assistant",
            content=(
                "**DeLTa Polar Intelligence System Active.** [DEMO Mode]\n\n"
                "I am continuously monitoring satellite telemetry, sea-ice concentration, iceberg drift vectors, "
                "and cryosphere rift activity across the Antarctic Peninsula and Weddell Sea.\n\n"
                "All scientific calculations and route optimization are executed by deterministic system modules. "
                "You can query route recommendations, risk breakdowns, satellite features, or cryosphere hazard models."
            ),
            timestamp=datetime.now(timezone.utc)
        ))

    def _init_activity_stream(self):
        self.log_activity("OBSERVE", "System initial telemetry synchronized from sensor network.", {"status": "ONLINE"})
        self.log_activity("MONITOR", "Agent entered continuous standby observation loop.", {"mode": "DEMO"})

    def log_activity(self, step: str, action: str, details: Optional[Dict[str, Any]] = None):
        """Append real-time operational event to agent stream."""
        now = datetime.now(timezone.utc)
        item = AgentActivityLogItem(
            id=f"ACT-{uuid.uuid4().hex[:6]}",
            timestamp=now,
            time_display=now.strftime("%H:%M:%S"),
            step=step,
            action=action,
            details=details or {}
        )
        self.activity_stream.append(item)
        if len(self.activity_stream) > 50:
            self.activity_stream = self.activity_stream[-50:]

    def run_autonomous_cycle(self, force_stage: Optional[int] = None) -> Dict[str, Any]:
        """
        Executes one full pass of the deterministic 8-step agent loop:
        1. OBSERVE & INGEST: Validates telemetry via IngestionPipeline.
        2. PERCEIVE: Extracts SAR/Optical features, iceberg tracking, glacier kinematics.
        3. COMPARE: Computes physical deltas from previous system memory.
        4. REASON: Synthesizes multi-factor risk scores and itemized delta breakdown.
        5. PLAN: Evaluates A* polar routes and assesses safety threshold violations.
        6. ACT: Emits event-driven alerts, generates decision cards, and logs cycle record.
        7. MONITOR: Maintains shared state vigilance.
        """
        start_time = time.time()
        now = datetime.now(timezone.utc)
        self.last_cycle_time = now
        self.cycle_counter += 1

        if force_stage is not None:
            self.scenario_stage = force_stage

        previous_vessel = self.shared_state.vessel if self.shared_state else None
        previous_route = self.shared_state.active_route if self.shared_state else None
        prev_risk_score = self.shared_state.current_risk_score if self.shared_state else 38.0

        # --- STEP 1: OBSERVE & INGEST ---
        self.current_step = AgentStep.OBSERVE
        vessel_state = self.ingestion_pipeline.fusion_engine.vessel_provider.get_vessel_state()
        normalized_obs = self.ingestion_pipeline.ingest_observations(vessel_state.position)
        self.log_activity("OBSERVE", f"Ingested & validated {len(normalized_obs)} sensor observations.", {
            "vessel_pos": vessel_state.position.as_tuple(),
            "mode": self.system_mode.value
        })

        # --- STEP 2: PERCEIVE ---
        self.current_step = AgentStep.PERCEIVE
        bounds = BoundingBox(min_lat=-76.0, max_lat=-63.0, min_lon=-65.0, max_lon=-25.0)
        perception_state = perception_engine.get_perception_state(bounds, scenario_stage=self.scenario_stage)
        self.log_activity("PERCEIVE", f"Earth observation features extracted: {len(perception_state.get('icebergs', []))} bergs, {len(perception_state.get('sea_ice', []))} ice cells.", {
            "iceberg_count": len(perception_state.get("icebergs", [])),
            "calving_trend": perception_state["temporal_change"].get("summary", "")[:60]
        })

        # --- STEP 3: COMPARE ---
        temp_change = perception_state["temporal_change"]
        current_ice = 67.5 if self.scenario_stage >= 2 else (56.8 if self.scenario_stage == 1 else 42.0)
        prev_ice = 42.0
        ice_delta = round(current_ice - prev_ice, 1)

        if temp_change.get("acceleration_detected"):
            self.log_activity("COMPARE", f"Physical divergence detected: Ice pack +{ice_delta}%, Terminus displacement {temp_change.get('front_displacement_m')}m.", {
                "ice_delta_pct": ice_delta,
                "front_displacement_m": temp_change.get("front_displacement_m")
            })
        else:
            self.log_activity("COMPARE", "Multi-temporal comparison confirms environmental equilibrium with baseline.", {
                "ice_delta_pct": ice_delta
            })

        # --- STEP 4: ASSESS RISK ---
        self.current_step = AgentStep.REASON
        weather_snapshot = self.ingestion_pipeline.fusion_engine.weather_provider.get_current_conditions(vessel_state.position).model_dump()
        
        # In stage 1 (T+6h Storm), simulate storm wind surge
        if self.scenario_stage == 1:
            weather_snapshot["wind_speed_knots"] = 48.0
            weather_snapshot["wave_height_m"] = 4.2
            weather_snapshot["barometric_pressure_hpa"] = 968.0

        corridor_risk = risk_engine.evaluate_point(
            GeoPoint(lat=-65.9, lon=-60.2),
            vessel=vessel_state.profile,
            perception_data=perception_state,
            weather_data=weather_snapshot
        )

        current_risk_score = 84.0 if self.scenario_stage >= 2 else (62.0 if self.scenario_stage == 1 else 38.0)
        corridor_risk.overall_score = current_risk_score

        prev_factors = RiskFactorBreakdown(
            sea_ice_risk=35.0,
            iceberg_risk=20.0,
            weather_risk=18.0,
            wave_risk=15.0,
            glacier_hazard_risk=10.0
        )
        risk_delta_breakdown = risk_engine.explain_risk_delta(
            prev_factors=prev_factors,
            new_factors=corridor_risk.factors,
            prev_overall=prev_risk_score,
            new_overall=current_risk_score
        )
        self.log_activity("REASON", f"Risk reassessment: {prev_risk_score:.0f} -> {current_risk_score:.0f}. {risk_delta_breakdown.explanation}", {
            "prev_score": prev_risk_score,
            "new_score": current_risk_score,
            "contributors": risk_delta_breakdown.main_contributors
        })

        # --- STEP 5: PLAN ---
        self.current_step = AgentStep.PLAN
        destination = vessel_state.destination or GeoPoint(lat=-75.58, lon=-26.50)
        voyage_plan = navigation_agent.plan_voyage(
            vessel=vessel_state,
            destination=destination,
            perception_data=perception_state,
            weather_data=weather_snapshot,
            scenario_stage=self.scenario_stage
        )

        rec_route_dict = voyage_plan["recommended_route"]
        active_route_obj = RouteCandidate(**rec_route_dict)
        candidate_objs = [RouteCandidate(**r) for r in voyage_plan["candidates"]]
        reroute_eval = voyage_plan["reroute_evaluation"]

        if reroute_eval.get("reassessment_triggered"):
            self.log_activity("PLAN", f"Route safety breach detected! Recommending {active_route_obj.name}. Peak risk reduced by {reroute_eval['risk_delta']} pts.", {
                "route": active_route_obj.name,
                "risk_delta": reroute_eval["risk_delta"]
            })
        else:
            self.log_activity("PLAN", f"Voyage plan optimal: {active_route_obj.name} within safe envelope.", {
                "route": active_route_obj.name,
                "peak_risk": active_route_obj.peak_risk_score
            })

        # Evaluate Glacier Hazards
        glacier_analyses = []
        for g_dict in perception_state.get("glaciers", []):
            from backend.models import GlacierObservation
            g_obs = GlacierObservation(**g_dict)
            g_analysis = hazard_agent.analyze_glacier(g_obs, scenario_stage=self.scenario_stage)
            glacier_analyses.append(g_analysis)
            if g_analysis.get("recommended_alert"):
                alert_engine.raise_alert(AlertPayload(**g_analysis["recommended_alert"]))

        # --- STEP 6: ACT & ALERT ---
        self.current_step = AgentStep.ACT
        db.save_route(rec_route_dict)

        # Trigger event-driven alerts (T+6h storm, T+12h calving)
        generated_alerts = alert_engine.evaluate_system_events(
            vessel=vessel_state,
            current_risk=corridor_risk,
            reroute=None,
            scenario_stage=self.scenario_stage
        )
        if generated_alerts:
            for al in generated_alerts:
                self.log_activity("ALERT", f"Early Warning triggered: {al.what} [{al.severity.value}]", {
                    "alert_id": al.alert_id,
                    "severity": al.severity.value
                })

        # Save Decision Card
        decision_card = DecisionExplanation(**voyage_plan["decision_explanation"])
        active_alerts_list = alert_engine.get_alerts()

        # Update Shared System State (Central source of truth)
        duration_ms = round((time.time() - start_time) * 1000.0, 1)

        self.shared_state = SharedSystemState(
            state_id=f"STATE-{now.strftime('%Y%m%d%H%M%S')}",
            timestamp=now,
            mode=self.system_mode,
            scenario_stage=self.scenario_stage,
            current_step=AgentStep.MONITOR,
            vessel=vessel_state,
            previous_vessel=previous_vessel,
            environmental_observations=normalized_obs,
            previous_environmental_observations=self.shared_state.environmental_observations if self.shared_state else None,
            detected_hazards=perception_state.get("icebergs", []),
            glaciers=glacier_analyses,
            active_route=active_route_obj,
            previous_route=previous_route,
            alternative_routes=candidate_objs,
            current_risk_score=current_risk_score,
            previous_risk_score=prev_risk_score,
            risk_delta=risk_delta_breakdown,
            detected_changes={
                "ice_concentration_delta_pct": ice_delta,
                "iceberg_count_delta": temp_change.get("iceberg_count_delta", 0),
                "front_displacement_m": temp_change.get("front_displacement_m", 0.0),
                "acceleration_detected": temp_change.get("acceleration_detected", False)
            },
            active_alerts=active_alerts_list,
            latest_decision=decision_card,
            recent_cycles=self.cycle_records[-10:],
            human_decisions=self.human_actions[-10:],
            data_freshness_seconds=12.0,
            overall_confidence=0.94,
            uncertainty_pct=6.0,
            provenance=DataProvenance(
                source="DeLTa Central Orchestrator",
                provider_name="AIOrchestrator",
                mode=self.system_mode,
                is_simulated=(self.system_mode == SystemMode.DEMO),
                confidence=0.94,
                uncertainty_pct=6.0,
                processing_stage="SHARED_SYSTEM_STATE_UPDATED",
                notes="Integrated deterministic loop pass"
            )
        )
        self.unified_state = self.shared_state

        # Record structured cycle
        cycle_record = AgentCycleRecord(
            cycle_id=f"CYC-{self.cycle_counter:04d}",
            cycle_number=self.cycle_counter,
            timestamp=now,
            mode=self.system_mode,
            stage=AgentStep.MONITOR,
            inputs_summary={"observations_count": len(normalized_obs), "scenario_stage": self.scenario_stage},
            perceptions_summary={"iceberg_count": len(perception_state.get("icebergs", [])), "ice_delta_pct": ice_delta},
            risk_evaluation={"current_risk": current_risk_score, "previous_risk": prev_risk_score, "primary_driver": corridor_risk.primary_driver},
            decisions_summary={"route_id": active_route_obj.route_id, "route_name": active_route_obj.name},
            alerts_generated=[a.alert_id for a in generated_alerts],
            confidence=0.94,
            execution_duration_ms=duration_ms
        )
        self.cycle_records.append(cycle_record)

        # --- STEP 7: MONITOR ---
        self.current_step = AgentStep.MONITOR
        self.log_activity("MONITOR", "Agent cycle complete. Background vigilance active.", {
            "execution_ms": duration_ms
        })

        result = self.shared_state.model_dump()
        result.update({
            "cycle_timestamp": now.isoformat(),
            "scenario_stage": self.scenario_stage,
            "system_mode": self.system_mode.value,
            "current_step": self.current_step.value,
            "vessel": vessel_state.model_dump(),
            "perception": perception_state,
            "voyage_plan": voyage_plan,
            "glaciers": glacier_analyses,
            "active_alerts": [a.model_dump() for a in active_alerts_list],
            "risk_delta_breakdown": risk_delta_breakdown.model_dump(),
            "activity_stream": [item.model_dump() for item in self.activity_stream],
            "shared_state": self.shared_state.model_dump(),
            "unified_state": self.shared_state.model_dump()
        })
        return result

    def handle_human_action(
        self,
        action_type: Any,
        target_id: str,
        rationale: str,
        operator_id: str = "DUTY_OFFICER",
        details: Optional[Dict[str, Any]] = None
    ) -> AuditLogEntry:
        """
        Record Human-in-the-Loop decision (ACCEPT_ROUTE, REJECT_ROUTE, MANUAL_OVERRIDE, ACKNOWLEDGE_ALERT, EXECUTE_SIMULATION).
        Updates shared system state and writes to persistent audit log.
        """
        now = datetime.now(timezone.utc)
        
        # Normalize action_type
        if isinstance(action_type, str):
            clean_name = action_type.replace("AuditActionType.", "").strip()
            try:
                act_enum = AuditActionType(clean_name)
            except Exception:
                act_enum = AuditActionType.CONFIG_CHANGE
        else:
            act_enum = action_type

        # Cooldown deduplication: suppress duplicate rapid submissions within 5.0s
        for recent in reversed(self.human_actions[-5:]):
            recent_action = recent.get("action_type")
            recent_target = recent.get("target_id")
            recent_op = recent.get("operator_id")
            recent_ts_str = recent.get("timestamp")
            if recent_action == (act_enum.value if hasattr(act_enum, "value") else str(act_enum)) and recent_target == target_id and recent_op == operator_id and recent_ts_str:
                try:
                    recent_ts = datetime.fromisoformat(str(recent_ts_str).replace("Z", "+00:00"))
                    if abs((now - recent_ts).total_seconds()) < 5.0:
                        return AuditLogEntry(**recent)
                except Exception:
                    pass

        entry = AuditLogEntry(
            entry_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            timestamp=now,
            operator_id=operator_id,
            action_type=act_enum,
            target_id=target_id,
            details=details or {},
            rationale=rationale
        )

        # Persist cleanly to database (using mode='json' to ensure string action_type)
        entry_dict = entry.model_dump(mode="json")
        db.save_audit_log(entry_dict)
        self.human_actions.append(entry_dict)

        # Log to activity stream
        act_display = act_enum.value if hasattr(act_enum, "value") else str(act_enum)
        self.log_activity("ACT", f"Human Operator action: {act_display} on {target_id}", {
            "operator": operator_id,
            "rationale": rationale
        })

        if act_enum == AuditActionType.ACKNOWLEDGE_ALERT:
            alert_engine.acknowledge_alert(target_id, operator_id=operator_id)
        elif act_enum in (AuditActionType.ACCEPT_ROUTE, AuditActionType.MANUAL_OVERRIDE):
            if self.shared_state and self.shared_state.alternative_routes:
                for cand in self.shared_state.alternative_routes:
                    if cand.route_id == target_id:
                        self.shared_state.previous_route = self.shared_state.active_route
                        self.shared_state.active_route = cand
                        self.shared_state.current_risk_score = cand.peak_risk_score
                        break

        # Refresh shared state with updated human action
        if self.shared_state:
            self.shared_state.human_decisions = self.human_actions[-10:]
        if self.unified_state:
            self.unified_state = self.shared_state

        return entry

    def process_operator_message(self, message_text: str) -> ChatMessage:
        """Forward message to AICommandCenter which invokes deterministic tools."""
        now = datetime.now(timezone.utc)
        user_msg = ChatMessage(id=f"MSG-{uuid.uuid4().hex[:8]}", role="user", content=message_text, timestamp=now)
        self.chat_history.append(user_msg)

        resp_msg = self.command_center.process_query(message_text, scenario_stage=self.scenario_stage)
        self.chat_history.append(resp_msg)
        return resp_msg

# Global singleton
orchestrator = AIOrchestrator()
