"""
Weather Provider Base Abstraction
"""

from abc import abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime
from backend.data_sources.base import BaseProvider
from backend.models import WeatherObservation, GeoPoint

class WeatherProvider(BaseProvider):
    def __init__(self, name: str, is_live: bool = False):
        super().__init__(name=name, is_live_source=is_live)

    @abstractmethod
    def get_current_conditions(self, point: GeoPoint) -> WeatherObservation:
        """Return current weather, wind, gust, waves, and freezing spray risk."""
        pass
