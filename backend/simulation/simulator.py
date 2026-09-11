"""
Simulation & Digital Twin Engine
Drives dynamic Antarctic environmental scenarios (Weddell Sea & Antarctic Peninsula).
Enables deterministic time-stepped simulation (T+0, T+6h, T+12h) to demonstrate end-to-end agent reactivity.
Adheres strictly to Requirement 5: Golden End-to-End Demo Scenario.
"""

from typing import Dict, Any
from datetime import datetime, timezone
import uuid
from backend.agents.orchestrator import orchestrator
from backend.models import SystemMode, AuditActionType
from backend.database.db import db

class PolarSimulator:
    def __init__(self):
        self.scenario_name = "Weddell Sea Calving & Katabatic Pack Ice Convergence"
        self.current_step_name = "T+0: Baseline Departure"
        self.stage = 0

    def step_to_stage(self, stage: int) -> Dict[str, Any]:
        """
        Advance or set simulation time step:
        - Stage 0: T+0 Baseline Departure (Nominal conditions, Route B active, Risk 38, Baseline ice velocity 2.4 m/d)
        - Stage 1: T+6h Storm Surge & Pressure Drop (968 hPa, 48 kt gusts, +14.8% ice drift, Risk 62, Warning alert)
        - Stage 2: T+12h Major Calving Event & Direct Obstruction (820m detachment, 5 tabular icebergs, Risk 84, Route Bravo compromised, Route Alpha recommended, Critical alert)
        """
        self.stage = stage
        if stage == 0:
            self.current_step_name = "T+0: Baseline Departure (Gerlache to Halley VI)"
        elif stage == 1:
            self.current_step_name = "T+6h: Storm Inflow & Pack Ice Compression"
        else:
            self.current_step_name = "T+12h: Major Calving Event & Active Rerouting"

        # Trigger the Orchestrator loop with the exact stage
        cycle_result = orchestrator.run_autonomous_cycle(force_stage=stage)

        # Log to audit trail and update shared state / activity stream
        orchestrator.handle_human_action(
            action_type=AuditActionType.EXECUTE_SIMULATION,
            target_id=f"STAGE_{stage}",
            details={"step_name": self.current_step_name, "stage": stage},
            rationale=f"Operator simulated environmental progression to {self.current_step_name} [DEMO Provenance]",
            operator_id="DUTY_OFFICER"
        )

        return {
            "scenario": self.scenario_name,
            "stage": self.stage,
            "step_name": self.current_step_name,
            "cycle_result": cycle_result
        }

    def trigger_sudden_calving_event(self) -> Dict[str, Any]:
        """One-click trigger demonstrating the complete autonomous agent response loop."""
        return self.step_to_stage(stage=2)

    def reset(self) -> Dict[str, Any]:
        """Reset scenario back to T+0 baseline."""
        return self.step_to_stage(stage=0)

# Global singleton
simulator = PolarSimulator()
