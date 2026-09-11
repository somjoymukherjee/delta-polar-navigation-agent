"""
Data Fusion & Normalization Engine
Unifies heterogeneous satellite, meteorological, oceanographic, and vessel data streams.
Performs quality assessment, staleness checks, and coordinate alignment.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from backend.models import (
    GeoPoint, BoundingBox, WeatherObservation, OceanObservation,
    SatelliteProduct, VesselState, DataQualityStatus
)
from backend.data_sources.satellite.synthetic_polar import SyntheticPolarSatelliteProvider
from backend.data_sources.weather.open_meteo_provider import OpenMeteoPolarProvider
from backend.data_sources.ocean.ocean_provider import OceanDataProvider
from backend.data_sources.vessel.vessel_provider import VesselDataProvider

class DataFusionEngine:
    def __init__(self, use_live_apis: bool = True):
        self.use_live_apis = use_live_apis
        self.satellite_provider = SyntheticPolarSatelliteProvider(is_demo=not use_live_apis)
        self.weather_provider = OpenMeteoPolarProvider(use_live_api=use_live_apis)
        self.ocean_provider = OceanDataProvider(is_live=use_live_apis)
        self.vessel_provider = VesselDataProvider()

    def set_live_mode(self, live: bool):
        self.use_live_apis = live
        self.weather_provider.use_live_api = live
        self.satellite_provider.is_demo = not live

    def get_normalized_observations(self, point: Optional[GeoPoint] = None) -> List[Dict[str, Any]]:
        """Return standardized internal observation objects across all sensors."""
        vessel = self.vessel_provider.get_vessel_state()
        pt = point or vessel.position
        weather = self.weather_provider.get_current_conditions(pt)
        ocean = self.ocean_provider.get_ocean_conditions(pt)
        mode = "LIVE" if self.use_live_apis else "DEMO"
        now = datetime.now(timezone.utc)

        observations = [
            {
                "source": weather.quality.source,
                "timestamp": weather.timestamp.isoformat(),
                "lat": pt.lat,
                "lon": pt.lon,
                "parameter": "wind_speed",
                "value": weather.wind_speed_knots,
                "unit": "knots",
                "confidence": weather.quality.confidence,
                "freshness_seconds": weather.quality.age_seconds,
                "quality": weather.quality.quality.value,
                "mode": mode
            },
            {
                "source": weather.quality.source,
                "timestamp": weather.timestamp.isoformat(),
                "lat": pt.lat,
                "lon": pt.lon,
                "parameter": "wave_height",
                "value": weather.wave_height_m,
                "unit": "meters",
                "confidence": weather.quality.confidence,
                "freshness_seconds": weather.quality.age_seconds,
                "quality": weather.quality.quality.value,
                "mode": mode
            },
            {
                "source": ocean.quality.source,
                "timestamp": ocean.timestamp.isoformat(),
                "lat": pt.lat,
                "lon": pt.lon,
                "parameter": "sea_surface_temp",
                "value": ocean.sea_surface_temp_c,
                "unit": "°C",
                "confidence": ocean.quality.confidence,
                "freshness_seconds": ocean.quality.age_seconds,
                "quality": ocean.quality.quality.value,
                "mode": mode
            },
            {
                "source": ocean.quality.source,
                "timestamp": ocean.timestamp.isoformat(),
                "lat": pt.lat,
                "lon": pt.lon,
                "parameter": "current_speed",
                "value": ocean.current_speed_knots,
                "unit": "knots",
                "confidence": ocean.quality.confidence,
                "freshness_seconds": ocean.quality.age_seconds,
                "quality": ocean.quality.quality.value,
                "mode": mode
            }
        ]
        return observations

    def get_unified_snapshot(self, point: Optional[GeoPoint] = None) -> Dict[str, Any]:
        """Aggregate aligned environmental and ship telemetry."""
        vessel = self.vessel_provider.get_vessel_state()
        query_pt = point or vessel.position

        weather = self.weather_provider.get_current_conditions(query_pt)
        ocean = self.ocean_provider.get_ocean_conditions(query_pt)

        bounds = BoundingBox(
            min_lat=query_pt.lat - 2.5,
            max_lat=query_pt.lat + 2.5,
            min_lon=query_pt.lon - 5.0,
            max_lon=query_pt.lon + 5.0
        )
        sat_passes = self.satellite_provider.fetch_latest_passes(bounds, limit=2)
        norm_obs = self.get_normalized_observations(query_pt)

        # Quality scoring
        qualities = [weather.quality.quality, ocean.quality.quality] + [p.quality.quality for p in sat_passes]
        has_stale = any(q == DataQualityStatus.STALE for q in qualities)
        has_degraded = any(q == DataQualityStatus.DEGRADED for q in qualities)
        
        overall_quality = "STALE" if has_stale else ("DEGRADED" if has_degraded else "OPTIMAL")
        overall_confidence = round(sum(p.quality.confidence for p in sat_passes) / max(1, len(sat_passes)), 2)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_point": query_pt.as_tuple(),
            "vessel": vessel.model_dump(),
            "weather": weather.model_dump(),
            "ocean": ocean.model_dump(),
            "satellite_passes": [p.model_dump() for p in sat_passes],
            "normalized_observations": norm_obs,
            "fusion_metadata": {
                "overall_quality": overall_quality,
                "overall_confidence": overall_confidence,
                "is_live_mode": self.use_live_apis,
                "data_mode": "LIVE" if self.use_live_apis else "DEMO",
                "aligned_sensors": ["Sentinel-1 SAR", "Sentinel-2 MSI", "Open-Meteo", "Copernicus Marine"]
            }
        }

# Global singleton
fusion_engine = DataFusionEngine(use_live_apis=False)
