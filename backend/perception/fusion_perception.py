"""
Unified Perception & Feature Fusion Layer
Integrates SAR, Optical, and Temporal Change Detection into cohesive cryospheric and navigational features.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from backend.models import (
    BoundingBox, GeoPoint, IcebergDetection, SeaIceObservation, GlacierObservation,
    TemporalChangeAnalysis, DataQualityStatus
)
from backend.perception.sar_processor import SARProcessor
from backend.perception.optical_processor import OpticalProcessor
from backend.perception.temporal_engine import TemporalChangeEngine

class PerceptionFusionEngine:
    def __init__(self):
        self.sar_processor = SARProcessor()
        self.optical_processor = OpticalProcessor()
        self.temporal_engine = TemporalChangeEngine()

    def get_perception_state(self, bounds: BoundingBox, scenario_stage: int = 0) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        
        # 1. SAR Iceberg Detection
        icebergs = self.sar_processor.detect_icebergs(bounds, now, scenario_stage=scenario_stage)

        # 2. Optical Lead and NDSI features
        optical_data = self.optical_processor.compute_ndsi_and_cloud_mask(bounds)
        leads = self.optical_processor.detect_optical_leads(bounds)

        # 3. Sea Ice Grids (Weddell Sea & Antarctic Peninsula navigation corridor)
        # Stage 0: moderate 42% pack ice; Stage 1+: high 68% compressed pack ice
        ice_conc = 42.0 if scenario_stage == 0 else 68.0
        stage_desc = "first_year_pack" if scenario_stage == 0 else "compressed_heavy_pack"
        thickness = 75.0 if scenario_stage == 0 else 140.0

        sea_ice_obs = [
            SeaIceObservation(
                grid_id="ICE_GRID_GERLACHE_SOUTH",
                bounds=BoundingBox(min_lat=-65.5, max_lat=-64.5, min_lon=-63.5, max_lon=-61.5),
                center=GeoPoint(lat=-65.0, lon=-62.5),
                concentration_pct=ice_conc,
                stage=stage_desc,
                thickness_cm=thickness,
                compression_risk="HIGH" if scenario_stage >= 1 else "LOW",
                confidence=0.92,
                sensor_type="Fused Sentinel-1 SAR & Sentinel-2 Optical",
                timestamp=now
            ),
            SeaIceObservation(
                grid_id="ICE_GRID_WEDDELL_NORTH",
                bounds=BoundingBox(min_lat=-67.0, max_lat=-65.5, min_lon=-61.5, max_lon=-57.0),
                center=GeoPoint(lat=-66.25, lon=-59.25),
                concentration_pct=min(95.0, ice_conc + 12.0),
                stage="heavy_rafted_pack",
                thickness_cm=thickness + 35.0,
                compression_risk="HIGH",
                confidence=0.95,
                sensor_type="Sentinel-1 SAR EW Mode",
                timestamp=now
            ),
            SeaIceObservation(
                grid_id="ICE_GRID_WEDDELL_OUTER",
                bounds=BoundingBox(min_lat=-66.5, max_lat=-64.5, min_lon=-56.0, max_lon=-50.0),
                center=GeoPoint(lat=-65.5, lon=-53.0),
                concentration_pct=24.0, # Safer offshore corridor
                stage="open_drift_ice",
                thickness_cm=45.0,
                compression_risk="LOW",
                confidence=0.88,
                sensor_type="Sentinel-1 SAR EW Mode",
                timestamp=now
            )
        ]

        # 4. Glacier Observation (e.g. Larsen C / Brunt Ice Shelf front)
        retreat_m = 120.0 if scenario_stage == 0 else 940.0
        velocity = 2.4 if scenario_stage == 0 else 4.8  # m/day
        accel = 0.05 if scenario_stage == 0 else 0.42   # m/day^2
        calving_act = "NORMAL_ABLATION" if scenario_stage == 0 else "MAJOR_CALVING_COLLAPSE"
        trend_status = "STEADY" if scenario_stage == 0 else "RAPID_ACCELERATION"

        glaciers = [
            GlacierObservation(
                glacier_id="GLACIER_LARSEN_C_FRONT",
                name="Larsen C Ice Shelf - Northern Rifts",
                front_position=GeoPoint(lat=-66.20, lon=-60.50),
                historical_baseline_front=GeoPoint(lat=-66.18, lon=-60.48),
                velocity_m_per_day=velocity,
                acceleration_m_per_day2=accel,
                retreat_distance_m=retreat_m,
                calving_activity=calving_act,
                estimated_ice_loss_rate_gt_yr=18.5 if scenario_stage == 0 else 42.0,
                trend=trend_status,
                confidence=0.93,
                timestamp=now
            ),
            GlacierObservation(
                glacier_id="GLACIER_BRUNT_ICE_SHELF",
                name="Brunt Ice Shelf / Chasm 1",
                front_position=GeoPoint(lat=-75.55, lon=-26.80),
                historical_baseline_front=GeoPoint(lat=-75.52, lon=-26.75),
                velocity_m_per_day=1.8,
                acceleration_m_per_day2=0.02,
                retreat_distance_m=65.0,
                calving_activity="WATCH",
                estimated_ice_loss_rate_gt_yr=8.2,
                trend="STABLE",
                confidence=0.89,
                timestamp=now
            )
        ]

        # 5. Temporal Change Analysis
        t0 = now - timedelta(days=5)
        temporal_analysis = self.temporal_engine.compare_observations(
            region_id="WEDDELL_PENINSULA_CORRIDOR",
            t0_time=t0,
            t1_time=now,
            scenario_stage=scenario_stage
        )

        return {
            "timestamp": now.isoformat(),
            "icebergs": [b.model_dump() for b in icebergs],
            "sea_ice": [s.model_dump() for s in sea_ice_obs],
            "glaciers": [g.model_dump() for g in glaciers],
            "optical_analysis": optical_data,
            "leads": leads,
            "temporal_change": temporal_analysis.model_dump(),
            "scenario_stage": scenario_stage,
            "fusion_provenance": "Sentinel-1 SAR + Sentinel-2 Optical Multi-Temporal Fusion [DEMO Mode | Synthetic Baseline | Confidence: 94.0%]"
        }

# Global singleton
perception_engine = PerceptionFusionEngine()
