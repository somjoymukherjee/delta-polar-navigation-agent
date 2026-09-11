"""
Polar Vessel Telemetry & Performance Provider
Tracks vessel position, Polar Class ice limits, heading, and fuel economy.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.models import VesselState, VesselProfile, GeoPoint, PolarClass
from backend.data_sources.base import BaseProvider

class VesselDataProvider(BaseProvider):
    def __init__(self, initial_profile: Optional[VesselProfile] = None):
        super().__init__(name="Shipboard Integrated Bridge System (IBS/AIS)", is_live_source=True)
        self.profile = initial_profile or VesselProfile(
            vessel_id="POLAR_EXPLORER_I",
            name="R/V Sir David Attenborough",
            polar_class=PolarClass.PC5,
            max_speed_knots=15.0,
            cruise_speed_knots=11.5,
            ice_breaking_capability_m=1.0,
            safe_ice_concentration_limit=65.0
        )
        
        # Default Antarctic voyage: Starting off King George Island / Gerlache Strait towards Weddell Sea / Halley VI
        # Lat: -64.82, Lon: -63.50 (Gerlache Strait)
        self.current_state = VesselState(
            profile=self.profile,
            position=GeoPoint(lat=-64.82, lon=-63.50),
            heading_deg=135.0,
            speed_knots=11.2,
            destination=GeoPoint(lat=-75.58, lon=-26.50), # Halley VI Research Station
            destination_name="Halley VI Research Station (Brunt Ice Shelf)",
            current_route_id="ROUTE_TIME_FIRST",
            status="UNDERWAY - NAVIGATING POLAR WATERS"
        )

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "status": "HEALTHY",
            "provider": self.name,
            "vessel_name": self.profile.name,
            "polar_class": self.profile.polar_class.value,
            "position": self.current_state.position.as_tuple()
        }

    def get_vessel_state(self) -> VesselState:
        self.current_state.timestamp = datetime.now(timezone.utc)
        return self.current_state

    def update_position(self, lat: float, lon: float, heading: float, speed: float):
        self.current_state.position = GeoPoint(lat=lat, lon=lon)
        self.current_state.heading_deg = heading
        self.current_state.speed_knots = speed
        self.current_state.timestamp = datetime.now(timezone.utc)

    def set_destination(self, lat: float, lon: float, name: str):
        self.current_state.destination = GeoPoint(lat=lat, lon=lon)
        self.current_state.destination_name = name
