"""
Agent C — Glacier & Cryosphere Hazard Early-Warning Agent
Monitors ice-shelf deformation, front retreat, velocity, acceleration,
generates scenario-based projections (Baseline, Accelerated, High-Change),
and executes the Downstream Hazard Assessment Engine.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from backend.models import (
    GlacierObservation, GlacierScenarioProjection, DownstreamHazardAssessment,
    HazardSeverity, HazardProbability, BoundingBox, GeoPoint, AlertSeverity, AlertPayload,
    PhysicalMechanismType, ObservationClassification, DataProvenance, SystemMode
)

class GlacierHazardAgent:
    def __init__(self):
        self.agent_name = "Cryosphere Hazard Intelligence Agent (Agent C)"

    def analyze_glacier(self, glacier_obs: GlacierObservation, scenario_stage: int = 0) -> Dict[str, Any]:
        """
        Evaluate ice dynamics, compute kinematic trends, and project downstream hazards.
        """
        # Baseline vs Accelerated scenario values
        v = glacier_obs.velocity_m_per_day
        a = glacier_obs.acceleration_m_per_day2
        retreat = glacier_obs.retreat_distance_m

        # Dynamic trends
        velocity_km_yr = round((v * 365.25) / 1000.0, 2)
        acceleration_status = "CRITICAL_SURGE" if a > 0.20 else ("ELEVATED" if a > 0.08 else "BASELINE_EQUILIBRIUM")
        
        # 1. Scenario-Based Projections
        scenarios = self._generate_scenario_projections(glacier_obs.name, velocity_km_yr, scenario_stage)

        # 2. Downstream Hazard Matrix Evaluation
        downstream_hazards = self._evaluate_downstream_hazards(glacier_obs, scenario_stage)

        # 3. Early Warning Alert Recommendation
        recommended_alert = None
        if scenario_stage >= 1 or a > 0.25 or retreat > 500.0:
            recommended_alert = AlertPayload(
                alert_id=f"ALERT-CRYO-{int(datetime.now(timezone.utc).timestamp())}",
                severity=AlertSeverity.CRITICAL,
                what=f"Major Calving Event & Ice-Shelf Structural Fracture Detected at {glacier_obs.name}",
                where_lat=glacier_obs.front_position.lat,
                where_lon=glacier_obs.front_position.lon,
                where_location_name=glacier_obs.name,
                when_timestamp=datetime.now(timezone.utc),
                evidence=(
                    f"Sentinel-1 SAR interferometry reveals +{a:.2f} m/day² acceleration in front movement. "
                    f"Temporal change detection verifies {retreat:.0f}m front detachment with {v:.1f} m/day forward flow. "
                    f"High radar coherence loss confirms major tabular calving event."
                ),
                confidence=glacier_obs.confidence,
                uncertainty_pct=round((1.0 - glacier_obs.confidence) * 100.0, 1),
                provenance=DataProvenance(
                    source="Glacier Hazard Early-Warning Agent",
                    provider_name="GlacierHazardAgent",
                    mode=SystemMode.DEMO,
                    is_simulated=True,
                    confidence=glacier_obs.confidence,
                    uncertainty_pct=round((1.0 - glacier_obs.confidence) * 100.0, 1),
                    processing_stage="CRYO_HAZARD_EVALUATION",
                    notes="Deterministic evaluation of kinematic ice shelf deformation"
                ),
                expected_development=(
                    "Calved tabular fragments (500m-1000m) will drift northeast under Antarctic Coastal Current (0.8 kt). "
                    "Dense brash ice and growlers expected within a 45 km radius over the next 48-72 hours."
                ),
                recommended_action=(
                    "Enforce immediate 30 NM navigation exclusion zone around Larsen C northern front. "
                    "Reroute all marine vessels to offshore deep-water channels. Elevate radar ice-watch."
                )
            )
        elif a > 0.05:
            recommended_alert = AlertPayload(
                alert_id=f"ALERT-CRYO-{int(datetime.now(timezone.utc).timestamp())}",
                severity=AlertSeverity.WATCH,
                what=f"Elevated Ice Velocity & Rift Propagation at {glacier_obs.name}",
                where_lat=glacier_obs.front_position.lat,
                where_lon=glacier_obs.front_position.lon,
                where_location_name=glacier_obs.name,
                when_timestamp=datetime.now(timezone.utc),
                evidence=f"Observed velocity is {v:.1f} m/day ({velocity_km_yr} km/yr) with minor positive acceleration.",
                confidence=0.88,
                uncertainty_pct=12.0,
                provenance=DataProvenance(
                    source="Glacier Hazard Early-Warning Agent",
                    provider_name="GlacierHazardAgent",
                    mode=SystemMode.DEMO,
                    is_simulated=True,
                    confidence=0.88,
                    uncertainty_pct=12.0,
                    processing_stage="CRYO_HAZARD_EVALUATION"
                ),
                expected_development="Continued gradual rift expansion under seasonal tidal flexing.",
                recommended_action="Maintain routine satellite pass monitoring and track iceberg drift coordinates."
            )

        return {
            "glacier_id": glacier_obs.glacier_id,
            "name": glacier_obs.name,
            "coordinates": glacier_obs.front_position.as_tuple(),
            "velocity_m_per_day": v,
            "velocity_km_per_year": velocity_km_yr,
            "acceleration_m_per_day2": a,
            "acceleration_status": acceleration_status,
            "retreat_distance_m": retreat,
            "calving_activity": glacier_obs.calving_activity,
            "estimated_ice_loss_rate_gt_yr": glacier_obs.estimated_ice_loss_rate_gt_yr,
            "scenarios": [s.model_dump() for s in scenarios],
            "downstream_hazards": [h.model_dump() for h in downstream_hazards],
            "recommended_alert": recommended_alert.model_dump() if recommended_alert else None
        }

    def _generate_scenario_projections(self, glacier_name: str, baseline_vel_km_yr: float, scenario_stage: int) -> List[GlacierScenarioProjection]:
        """
        Produce scenario-based bounds without false precision.
        """
        mult = 1.6 if scenario_stage >= 1 else 1.0

        return [
            GlacierScenarioProjection(
                scenario_name="Baseline Scenario (Current Climate Trend)",
                description="Continuation of 2015-2025 decadal thermal and ocean circulation patterns.",
                annual_ice_loss_range_gt=(round(12.0 * mult, 1), round(22.0 * mult, 1)),
                retreat_velocity_range_m_yr=(round(baseline_vel_km_yr * 1000 * 0.95, 0), round(baseline_vel_km_yr * 1000 * 1.15, 0)),
                estimated_shelf_destabilization_window_years=(35.0, 50.0),
                confidence=0.89,
                assumptions=[
                    "Ocean water temperature at grounding line remains within ±0.3°C of present mean",
                    "Surface melt season duration does not exceed 75 days/year",
                    "Backstress from rumples and ice rises remains mechanically intact"
                ]
            ),
            GlacierScenarioProjection(
                scenario_name="Accelerated Warming Scenario (+1.5°C Ocean Thermal Forcing)",
                description="Enhanced Modified Circumpolar Deep Water (MCDW) intrusion beneath the floating ice shelf.",
                annual_ice_loss_range_gt=(round(25.0 * mult, 1), round(45.0 * mult, 1)),
                retreat_velocity_range_m_yr=(round(baseline_vel_km_yr * 1000 * 1.35, 0), round(baseline_vel_km_yr * 1000 * 1.75, 0)),
                estimated_shelf_destabilization_window_years=(18.0, 28.0),
                confidence=0.82,
                assumptions=[
                    "Basal melt rates increase by 40-60% along the inner pinning points",
                    "Hydrofracture occurs due to increased summer surface ponding",
                    "Sea-ice buttressing along front diminishes during winter months"
                ]
            ),
            GlacierScenarioProjection(
                scenario_name="High-Change Structural Collapse Scenario",
                description="Unpinning from seafloor bathymetric highs followed by runaway marine ice cliff instability (MICI).",
                annual_ice_loss_range_gt=(round(50.0 * mult, 1), round(85.0 * mult, 1)),
                retreat_velocity_range_m_yr=(round(baseline_vel_km_yr * 1000 * 2.2, 0), round(baseline_vel_km_yr * 1000 * 3.5, 0)),
                estimated_shelf_destabilization_window_years=(6.0, 14.0),
                confidence=0.74,
                assumptions=[
                    "Rapid ungrounding from retrograde bed slopes",
                    "Major transverse rift propagation cutting entire shelf width",
                    "Catastrophic tabular iceberg release similar to Larsen B (2002)"
                ]
            )
        ]

    def _evaluate_downstream_hazards(self, glacier_obs: GlacierObservation, scenario_stage: int) -> List[DownstreamHazardAssessment]:
        """
        Downstream Hazard Assessment Matrix.
        Evaluates plausible downstream consequences: navigation hazards, calving waves, GLOF, coastal impact.
        """
        lat = glacier_obs.front_position.lat
        lon = glacier_obs.front_position.lon
        bounds = BoundingBox(min_lat=lat - 1.5, max_lat=lat + 1.5, min_lon=lon - 3.0, max_lon=lon + 3.0)

        hazards = []

        # 1. Navigation Hazard from Calving & Bergs
        calving_sev = HazardSeverity.CRITICAL if scenario_stage >= 1 else HazardSeverity.MEDIUM
        calving_prob = HazardProbability.VERY_HIGH if scenario_stage >= 1 else HazardProbability.MEDIUM
        hazards.append(DownstreamHazardAssessment(
            hazard_type="Iceberg / Calving Navigation Hazard",
            severity=calving_sev,
            probability=calving_prob,
            physical_mechanism=PhysicalMechanismType.CALVING_DETACHMENT,
            observation_classification=ObservationClassification.DERIVED,
            confidence=0.94,
            uncertainty_pct=6.0,
            provenance=DataProvenance(
                source="Glacier Hazard Agent",
                provider_name="GlacierHazardAgent",
                mode=SystemMode.DEMO,
                is_simulated=True,
                confidence=0.94,
                uncertainty_pct=6.0,
                processing_stage="DOWNSTREAM_HAZARD_MODELING"
            ),
            time_horizon="Immediate (0-24 hours)",
            affected_area_bounds=bounds,
            downstream_impact_summary=(
                "Fresh tabular icebergs and semi-submerged growlers dispersed directly across regional shipping lanes. "
                "High collision risk for non-ice-strengthened vessels."
            ),
            recommended_action="Execute vessel dynamic reroute to maintain minimum 25 NM buffer from calving coordinates."
        ))

        # 2. Calving Tsunami / Impact Waves
        wave_sev = HazardSeverity.HIGH if scenario_stage >= 1 else HazardSeverity.LOW
        wave_prob = HazardProbability.HIGH if scenario_stage >= 1 else HazardProbability.LOW
        hazards.append(DownstreamHazardAssessment(
            hazard_type="Calving Impact Displacement Wave",
            severity=wave_sev,
            probability=wave_prob,
            physical_mechanism=PhysicalMechanismType.DISPLACEMENT_WAVE,
            observation_classification=ObservationClassification.DERIVED,
            confidence=0.86,
            uncertainty_pct=14.0,
            provenance=DataProvenance(
                source="Glacier Hazard Agent",
                provider_name="GlacierHazardAgent",
                mode=SystemMode.DEMO,
                is_simulated=True,
                confidence=0.86,
                uncertainty_pct=14.0,
                processing_stage="DOWNSTREAM_HAZARD_MODELING"
            ),
            time_horizon="Transient (0-2 hours post-calving)",
            affected_area_bounds=bounds,
            downstream_impact_summary=(
                "Localized displacement surge waves (3m - 7m crest) originating at calving front. "
                "Extreme danger for small craft, scientific zodiacs, and shallow anchorages."
            ),
            recommended_action="Immediate suspension of small boat operations within 15 km of ice front."
        ))

        # 3. Ice-Shelf Structural Instability
        hazards.append(DownstreamHazardAssessment(
            hazard_type="Ice-Shelf Structural Fracture & Fast Ice Destabilization",
            severity=HazardSeverity.HIGH if scenario_stage >= 1 else HazardSeverity.MEDIUM,
            probability=HazardProbability.HIGH if scenario_stage >= 1 else HazardProbability.LOW,
            physical_mechanism=PhysicalMechanismType.ICE_SHELF_RIFT,
            observation_classification=ObservationClassification.PROJECTED,
            confidence=0.91,
            uncertainty_pct=9.0,
            provenance=DataProvenance(
                source="Glacier Hazard Agent",
                provider_name="GlacierHazardAgent",
                mode=SystemMode.DEMO,
                is_simulated=True,
                confidence=0.91,
                uncertainty_pct=9.0,
                processing_stage="DOWNSTREAM_HAZARD_MODELING"
            ),
            time_horizon="Short-term (1-7 days)",
            affected_area_bounds=bounds,
            downstream_impact_summary=(
                "Loss of front buttressing triggers unzipping of adjacent shear margins. "
                "Shorefast ice breakout may trap vessels anchored near coastal ice cliffs."
            ),
            recommended_action="Field research teams on fast ice must evacuate; vessels clear shelf anchorages."
        ))

        return hazards

# Global singleton
hazard_agent = GlacierHazardAgent()
