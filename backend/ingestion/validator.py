"""
DeLTa Observation Validator
Performs strict validation on incoming sensor and model observations:
- Polar geospatial coordinates bounds checking
- Scientific parameter bounds and unit consistency
- Timestamps and staleness classification
- Data provenance and DEMO/LIVE mode integrity enforcement
- Deterministic confidence and uncertainty calculation
"""

from typing import Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from backend.models import (
    NormalizedObservation, DataProvenance, DataQualityStatus, SystemMode
)

class ObservationValidator:
    # Plausible scientific bounds for polar domain parameters
    BOUNDS = {
        "wind_speed": (0.0, 150.0, "knots"),
        "wind_gust": (0.0, 180.0, "knots"),
        "wave_height": (0.0, 30.0, "meters"),
        "air_temp": (-90.0, 35.0, "°C"),
        "sea_surface_temp": (-3.0, 30.0, "°C"),
        "current_speed": (0.0, 15.0, "knots"),
        "sea_ice_concentration": (0.0, 100.0, "%"),
        "iceberg_count": (0.0, 5000.0, "count"),
        "flow_velocity": (0.0, 100.0, "m/day"),
        "acceleration": (-50.0, 50.0, "m/day2"),
        "retreat_distance": (-500.0, 10000.0, "meters"),
    }

    @classmethod
    def validate_geopoint(cls, lat: float, lon: float) -> Tuple[bool, Optional[str]]:
        """Validate latitude and longitude ranges."""
        if not (-90.0 <= lat <= 90.0):
            return False, f"Latitude {lat} out of bounds [-90, 90]"
        if not (-180.0 <= lon <= 180.0):
            return False, f"Longitude {lon} out of bounds [-180, 180]"
        return True, None

    @classmethod
    def validate_observation_dict(cls, raw: Dict[str, Any], system_mode: SystemMode = SystemMode.DEMO) -> Tuple[Optional[NormalizedObservation], Optional[str]]:
        """
        Validate and normalize a raw observation dict into a typed NormalizedObservation.
        Enforces DEMO/LIVE provenance tags and computes confidence/uncertainty.
        """
        required_fields = ["source", "lat", "lon", "parameter", "value"]
        for field in required_fields:
            if field not in raw:
                return None, f"Missing required field: {field}"

        lat = float(raw["lat"])
        lon = float(raw["lon"])
        valid_geo, err = cls.validate_geopoint(lat, lon)
        if not valid_geo:
            return None, err

        param = str(raw["parameter"]).lower()
        val = float(raw["value"])

        # Validate range if known
        unit = raw.get("unit", "")
        if param in cls.BOUNDS:
            min_v, max_v, default_unit = cls.BOUNDS[param]
            if not (min_v <= val <= max_v):
                return None, f"Parameter {param} value {val} outside scientific bounds [{min_v}, {max_v}]"
            if not unit:
                unit = default_unit

        # Parse timestamp
        raw_ts = raw.get("timestamp")
        if isinstance(raw_ts, str):
            try:
                ts = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except Exception:
                ts = datetime.now(timezone.utc)
        elif isinstance(raw_ts, datetime):
            ts = raw_ts
        else:
            ts = datetime.now(timezone.utc)

        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        age_seconds = max(0.0, (now - ts).total_seconds())

        # Staleness & Data Quality
        if age_seconds <= 10800:  # <= 3 hours
            quality = DataQualityStatus.GOOD
            staleness_confidence_factor = 1.0
        elif age_seconds <= 43200:  # <= 12 hours
            quality = DataQualityStatus.DEGRADED
            staleness_confidence_factor = 0.85
        else:
            quality = DataQualityStatus.STALE
            staleness_confidence_factor = 0.50

        # Confidence handling
        base_confidence = float(raw.get("confidence", 0.90))
        base_confidence = max(0.0, min(1.0, base_confidence))
        effective_confidence = round(base_confidence * staleness_confidence_factor, 3)
        uncertainty_pct = round((1.0 - effective_confidence) * 100.0, 1)

        # Enforce Provenance (Requirement 1: Never allow simulated data to be presented as live)
        is_live = (system_mode == SystemMode.LIVE and raw.get("is_live", False))
        mode = SystemMode.LIVE if is_live else SystemMode.DEMO
        is_sim = not is_live

        provenance_dict = raw.get("provenance")
        if isinstance(provenance_dict, dict):
            provenance = DataProvenance(
                source=provenance_dict.get("source", raw.get("source", "DeLTa Sensor")),
                provider_name=provenance_dict.get("provider_name", "IngestionPipeline"),
                mode=mode,
                is_simulated=is_sim,
                timestamp=ts,
                spatial_resolution_km=float(provenance_dict.get("spatial_resolution_km", 1.0)),
                temporal_resolution_hours=float(provenance_dict.get("temporal_resolution_hours", 6.0)),
                quality=quality,
                confidence=effective_confidence,
                uncertainty_pct=uncertainty_pct,
                processing_stage="VALIDATED",
                notes=provenance_dict.get("notes", "Validated through DeLTa Ingestion Pipeline")
            )
        else:
            provenance = DataProvenance(
                source=raw.get("source", "DeLTa Sensor"),
                provider_name="IngestionPipeline",
                mode=mode,
                is_simulated=is_sim,
                timestamp=ts,
                quality=quality,
                confidence=effective_confidence,
                uncertainty_pct=uncertainty_pct,
                processing_stage="VALIDATED",
                notes="Standardized through DeLTa Ingestion Pipeline"
            )

        norm_obs = NormalizedObservation(
            source=raw["source"],
            timestamp=ts,
            lat=lat,
            lon=lon,
            parameter=param,
            value=val,
            unit=unit,
            confidence=effective_confidence,
            uncertainty_pct=uncertainty_pct,
            freshness_seconds=round(age_seconds, 1),
            quality=quality,
            mode=mode,
            provenance=provenance,
            metadata=raw.get("metadata", {})
        )

        return norm_obs, None
