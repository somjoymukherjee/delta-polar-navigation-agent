"""
DeLTa Ingestion Pipeline
Coordinates multi-modal data providers (Weather, Ocean, Satellite, Vessel),
validates all incoming telemetry, tags provenance, and emits unified NormalizedObservations.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from backend.models import (
    GeoPoint, NormalizedObservation, SystemMode, DataProvenance
)
from backend.data_sources.fusion import DataFusionEngine
from backend.ingestion.validator import ObservationValidator

class IngestionPipeline:
    def __init__(self, mode: SystemMode = SystemMode.DEMO):
        self.mode = mode
        self.fusion_engine = DataFusionEngine(use_live_apis=(mode == SystemMode.LIVE))
        self.ingestion_history: List[NormalizedObservation] = []
        self.validation_errors: List[str] = []

    def set_mode(self, mode: SystemMode):
        self.mode = mode
        self.fusion_engine.set_live_mode(mode == SystemMode.LIVE)

    def ingest_observations(self, point: Optional[GeoPoint] = None) -> List[NormalizedObservation]:
        """
        Pull observations from fusion engine, validate each one, tag provenance,
        and return normalized typed observations.
        """
        raw_list = self.fusion_engine.get_normalized_observations(point)
        validated_observations: List[NormalizedObservation] = []

        for raw in raw_list:
            norm_obs, err = ObservationValidator.validate_observation_dict(raw, system_mode=self.mode)
            if norm_obs:
                validated_observations.append(norm_obs)
            else:
                self.validation_errors.append(f"Observation validation failed: {err}")

        # Keep last 200 in memory
        self.ingestion_history.extend(validated_observations)
        self.ingestion_history = self.ingestion_history[-200:]

        return validated_observations

    def get_latest_observations(self) -> List[NormalizedObservation]:
        return self.ingestion_history[-20:] if self.ingestion_history else []
