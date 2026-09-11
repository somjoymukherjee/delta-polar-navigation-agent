"""
Base Data Provider Abstraction & Quality Assessment
Includes formal interface specifications for future NASA/Copernicus live integrations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from backend.models import (
    DataQualityReport, DataQualityStatus, DataProvenance, SystemMode,
    GeoPoint, BoundingBox, NormalizedObservation
)

class BaseProvider(ABC):
    def __init__(self, name: str, is_live_source: bool = False, mode: SystemMode = SystemMode.DEMO):
        self.name = name
        self.is_live_source = is_live_source
        self.mode = mode if is_live_source else SystemMode.DEMO

    @abstractmethod
    def get_health_status(self) -> Dict[str, Any]:
        """Return provider status, latency, and connection metrics."""
        pass

    def evaluate_quality(self, timestamp: datetime, spatial_res_km: float = 1.0, max_age_hours: float = 6.0) -> DataQualityReport:
        """Standardized quality and freshness calculation."""
        now = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        age_seconds = max(0.0, (now - timestamp).total_seconds())
        age_hours = age_seconds / 3600.0

        if age_hours <= max_age_hours:
            quality = DataQualityStatus.GOOD
            confidence = 0.95 - (age_hours / max_age_hours) * 0.15
        elif age_hours <= max_age_hours * 3:
            quality = DataQualityStatus.DEGRADED
            confidence = 0.70 - (age_hours / (max_age_hours * 3)) * 0.25
        else:
            quality = DataQualityStatus.STALE
            confidence = 0.35

        return DataQualityReport(
            source=self.name,
            timestamp=timestamp,
            age_seconds=round(age_seconds, 1),
            spatial_resolution_km=spatial_res_km,
            quality=quality,
            confidence=round(confidence, 2),
            processing_status="VALIDATED",
            is_live=self.is_live_source
        )

    def create_provenance(
        self,
        timestamp: datetime,
        spatial_resolution_km: float = 1.0,
        temporal_resolution_hours: float = 6.0,
        notes: Optional[str] = None
    ) -> DataProvenance:
        """Create explicit provenance object retaining DEMO/LIVE mode tag."""
        quality_report = self.evaluate_quality(timestamp, spatial_resolution_km)
        uncertainty = round((1.0 - quality_report.confidence) * 100.0, 1)
        return DataProvenance(
            source=self.name,
            provider_name=self.__class__.__name__,
            mode=SystemMode.LIVE if self.is_live_source else SystemMode.DEMO,
            is_simulated=not self.is_live_source,
            timestamp=timestamp,
            spatial_resolution_km=spatial_resolution_km,
            temporal_resolution_hours=temporal_resolution_hours,
            quality=quality_report.quality,
            confidence=quality_report.confidence,
            uncertainty_pct=uncertainty,
            processing_stage="INGESTION_STANDARDIZED",
            notes=notes or ("Simulated benchmark telemetry" if not self.is_live_source else "Live sensor feed")
        )

# ---------------------------------------------------------------------------
# Future Live Provider Abstractions (Requirement 4)
# ---------------------------------------------------------------------------

class FutureNASAEarthdataProvider(BaseProvider):
    """
    Interface definition for future NASA Earthdata / CMR / GIBS integration.
    Do not invoke external endpoints until live credentials are configured.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="NASA-Earthdata-CMR", is_live_source=False, mode=SystemMode.DEMO)
        self.api_key = api_key
        self.is_configured = bool(api_key)

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "status": "READY_FOR_INTEGRATION" if not self.is_configured else "CONFIGURED",
            "is_live": False,
            "endpoint": "https://cmr.earthdata.nasa.gov/search/granules.json",
            "supported_collections": ["MODIS_Terra_L2", "VIIRS_NPP", "ICESat-2_ATL06"]
        }

    def search_granules(self, bounding_box: BoundingBox, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Search NASA CMR metadata catalog (Interface stub ready for future live API integration)."""
        if not self.is_configured:
            return []
        return []


class FutureCopernicusMarineProvider(BaseProvider):
    """
    Interface definition for future Copernicus Marine Service (CMEMS) API.
    """
    def __init__(self, credentials: Optional[Dict[str, str]] = None):
        super().__init__(name="Copernicus-Marine-Service", is_live_source=False, mode=SystemMode.DEMO)
        self.credentials = credentials
        self.is_configured = bool(credentials)

    def get_health_status(self) -> Dict[str, Any]:
        return {
            "provider": self.name,
            "status": "READY_FOR_INTEGRATION" if not self.is_configured else "CONFIGURED",
            "is_live": False,
            "endpoint": "https://cmems.copernicus.eu/api",
            "supported_products": ["SEAICE_GLO_SEAICE_L4_NRT_OBSERVATIONS_011_001"]
        }
