"""
Satellite Provider Abstraction
"""

from abc import abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from backend.data_sources.base import BaseProvider
from backend.models import SatelliteProduct, BoundingBox, DataQualityReport

class SatelliteProvider(BaseProvider):
    def __init__(self, name: str, sensor_type: str, is_live: bool = False):
        super().__init__(name=name, is_live_source=is_live)
        self.sensor_type = sensor_type

    @abstractmethod
    def fetch_latest_passes(self, bounds: BoundingBox, limit: int = 5) -> List[SatelliteProduct]:
        """Fetch newest satellite acquisition products matching bounding box."""
        pass

    @abstractmethod
    def fetch_temporal_pair(self, bounds: BoundingBox, target_date: Optional[datetime] = None) -> Tuple[SatelliteProduct, SatelliteProduct]:
        """Fetch a temporal pair (T0 historical baseline vs T1 recent) for change detection."""
        pass
