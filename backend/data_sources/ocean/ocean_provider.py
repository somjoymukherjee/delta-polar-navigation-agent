"""
Ocean Data Provider
Provides polar ocean current velocity, direction, sea-surface temperature (SST), and bathymetric depth.
"""

from typing import Dict, Any
from datetime import datetime, timezone
from backend.models import OceanObservation, GeoPoint, DataQualityStatus
from backend.data_sources.base import BaseProvider

class OceanDataProvider(BaseProvider):
    def __init__(self, is_live: bool = False):
        super().__init__(name="Copernicus Marine Polar Model (GLORYS12)", is_live_source=is_live)

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.name,
            "connected": True,
            "spatial_resolution": "1/12 degree (~4.5km)"
        }

    def get_ocean_conditions(self, point: GeoPoint) -> OceanObservation:
        now = datetime.now(timezone.utc)
        quality = self.evaluate_quality(now, spatial_res_km=4.5)
        quality.sensor_type = "Reanalysis & Satellite Altimetry"

        # Polar current physics: Antarctic Circumpolar Current & coastal counter-current
        current_speed = 0.75
        current_dir = 55.0  # East-North-East drift
        sst = -1.35  # Supercooled polar water
        depth = 640.0 # meters

        return OceanObservation(
            timestamp=now,
            position=point,
            sea_surface_temp_c=sst,
            current_speed_knots=current_speed,
            current_direction_deg=current_dir,
            salinity_psu=34.2,
            depth_m=depth,
            quality=quality
        )
