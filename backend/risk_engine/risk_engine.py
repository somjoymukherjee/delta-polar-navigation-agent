"""
Central Geographic Risk Engine
Unified multi-factor 0-100 spatial risk scoring for Antarctic navigation and cryosphere operations.
Integrates sea ice, icebergs, weather, waves, currents, glacier hazards, ASPA zones, and data quality.
"""

import math
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone
from backend.models import (
    GeoPoint, BoundingBox, RiskScore, RiskCategory, RiskFactorBreakdown,
    RiskGridCell, VesselProfile, PolarClass, RiskDeltaBreakdown, DataProvenance, SystemMode
)

class CentralRiskEngine:
    def __init__(self):
        # Configurable weightings (sum to 1.0)
        self.weights = {
            "sea_ice": 0.35,
            "iceberg": 0.25,
            "weather": 0.15,
            "wave": 0.10,
            "glacier_hazard": 0.10,
            "freshness": 0.05
        }
        
        # ASPA (Antarctic Specially Protected Areas) boundaries - strict navigation penalty
        self.restricted_zones = [
            {"name": "ASPA 152 - Western Bransfield Strait", "min_lat": -63.5, "max_lat": -63.1, "min_lon": -62.5, "max_lon": -61.8},
            {"name": "ASPA 126 - Byers Peninsula", "min_lat": -62.7, "max_lat": -62.5, "min_lon": -61.3, "max_lon": -60.8},
        ]

    def _haversine_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        r = 6371.0
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)
        a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
        return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    def evaluate_point(
        self,
        point: GeoPoint,
        vessel: Optional[VesselProfile] = None,
        perception_data: Optional[Dict[str, Any]] = None,
        weather_data: Optional[Dict[str, Any]] = None
    ) -> RiskScore:
        """
        Compute multi-factor risk score (0-100) at specific Antarctic coordinates.
        """
        vessel_profile = vessel or VesselProfile()

        # 1. Sea Ice Risk calculation
        ice_risk = 20.0 # baseline open polar water
        sea_ice_list = (perception_data or {}).get("sea_ice", [])
        for grid in sea_ice_list:
            bounds = grid.get("bounds", {})
            if (bounds.get("min_lat", -90) <= point.lat <= bounds.get("max_lat", 90) and
                bounds.get("min_lon", -180) <= point.lon <= bounds.get("max_lon", 180)):
                conc = grid.get("concentration_pct", 30.0)
                # Compare against vessel polar class capability
                safe_limit = vessel_profile.safe_ice_concentration_limit
                if conc > safe_limit:
                    excess = conc - safe_limit
                    ice_risk = min(100.0, 60.0 + excess * 1.5)
                else:
                    ice_risk = (conc / safe_limit) * 55.0
                break

        # 2. Iceberg Proximity & Density Risk
        berg_risk = 0.0
        icebergs = (perception_data or {}).get("icebergs", [])
        closest_berg_dist = 999.0
        for berg in icebergs:
            pos = berg.get("position", {})
            b_lat = pos.get("lat", 0.0)
            b_lon = pos.get("lon", 0.0)
            dist_km = self._haversine_km(point.lat, point.lon, b_lat, b_lon)
            if dist_km < closest_berg_dist:
                closest_berg_dist = dist_km
            
            # High threat if within 15 km
            if dist_km < 15.0:
                threat = (15.0 - dist_km) / 15.0 * 85.0
                berg_risk = max(berg_risk, threat)

        # 3. Weather & Freezing Spray Risk
        weather = weather_data or {}
        wind_spd = weather.get("wind_speed_knots", 22.0)
        temp_c = weather.get("air_temp_c", -6.0)
        weather_risk = min(100.0, (wind_spd / 45.0) * 70.0)
        if temp_c < -5.0 and wind_spd > 25.0:
            weather_risk = min(100.0, weather_risk + 25.0) # Freezing spray hazard

        # 4. Wave & Swell Risk
        wave_height = weather.get("wave_height_m", 2.5)
        wave_risk = min(100.0, (wave_height / 7.0) * 100.0)

        # 5. Glacier Calving & Cryosphere Hazard Risk
        glacier_risk = 0.0
        glaciers = (perception_data or {}).get("glaciers", [])
        for g in glaciers:
            front = g.get("front_position", {})
            g_dist = self._haversine_km(point.lat, point.lon, front.get("lat", 0), front.get("lon", 0))
            if g_dist < 40.0:
                act = g.get("calving_activity", "MODERATE")
                mult = 2.2 if "CALVING" in act or "COLLAPSE" in act else 1.0
                glacier_risk = max(glacier_risk, min(100.0, (40.0 - g_dist) / 40.0 * 75.0 * mult))

        # 6. Restricted ASPA Zone Penalty
        restricted_penalty = 0.0
        for z in self.restricted_zones:
            if z["min_lat"] <= point.lat <= z["max_lat"] and z["min_lon"] <= point.lon <= z["max_lon"]:
                restricted_penalty = 100.0
                break

        # 7. Data Freshness & Uncertainty
        freshness_penalty = 5.0

        # Weighted sum
        composite = (
            self.weights["sea_ice"] * ice_risk +
            self.weights["iceberg"] * berg_risk +
            self.weights["weather"] * weather_risk +
            self.weights["wave"] * wave_risk +
            self.weights["glacier_hazard"] * glacier_risk +
            self.weights["freshness"] * freshness_penalty
        )
        if restricted_penalty > 0:
            composite = max(composite, restricted_penalty)

        overall_score = round(max(0.0, min(100.0, composite)), 1)

        # Categorize
        if overall_score <= 20.0:
            cat = RiskCategory.SAFE
        elif overall_score <= 40.0:
            cat = RiskCategory.LOW
        elif overall_score <= 60.0:
            cat = RiskCategory.MODERATE
        elif overall_score <= 80.0:
            cat = RiskCategory.HIGH
        else:
            cat = RiskCategory.EXTREME

        # Determine primary driver
        factor_scores = {
            "Sea Ice Concentration": ice_risk,
            "Iceberg Collision Probability": berg_risk,
            "Gale Wind & Freezing Spray": weather_risk,
            "Rough Ocean Swell": wave_risk,
            "Cryosphere Calving Hazard": glacier_risk,
            "Restricted Environmental Zone": restricted_penalty
        }
        primary_driver = max(factor_scores, key=factor_scores.get)

        # Human-readable explanation
        reasons = []
        if ice_risk > 50:
            reasons.append(f"High sea-ice density ({ice_risk:.0f}/100) exceeding vessel polar tolerance")
        if berg_risk > 45:
            reasons.append(f"Proximate radar-detected icebergs within navigation corridor ({closest_berg_dist:.1f} km)")
        if glacier_risk > 40:
            reasons.append(f"Active ice-shelf rift & calving hazard zone")
        if weather_risk > 50:
            reasons.append(f"Severe gale wind & icing spray conditions")
        if restricted_penalty > 0:
            reasons.append(f"Penetrates ASPA designated biological conservation boundary")

        explanation = "; ".join(reasons) if reasons else "Favorable navigational conditions within Polar Class PC5 operating envelope."
        confidence = 0.92
        uncertainty_pct = 8.0

        return RiskScore(
            overall_score=overall_score,
            category=cat,
            primary_driver=primary_driver,
            factors=RiskFactorBreakdown(
                sea_ice_risk=round(ice_risk, 1),
                iceberg_risk=round(berg_risk, 1),
                weather_risk=round(weather_risk, 1),
                wave_risk=round(wave_risk, 1),
                glacier_hazard_risk=round(glacier_risk, 1),
                restricted_zone_penalty=round(restricted_penalty, 1),
                data_freshness_penalty=round(freshness_penalty, 1),
                model_uncertainty_penalty=3.0
            ),
            explanation=explanation,
            confidence=confidence,
            uncertainty_pct=uncertainty_pct,
            provenance=DataProvenance(
                source="DeLTa Central Risk Engine",
                provider_name="CentralRiskEngine",
                mode=SystemMode.DEMO,
                is_simulated=True,
                confidence=confidence,
                uncertainty_pct=uncertainty_pct,
                processing_stage="DETERMINISTIC_SCORING",
                notes="Deterministic multi-factor spatial risk evaluation"
            ),
            timestamp=datetime.now(timezone.utc)
        )

    def generate_risk_grid(
        self,
        bounds: BoundingBox,
        steps_lat: int = 8,
        steps_lon: int = 10,
        perception_data: Optional[Dict[str, Any]] = None,
        weather_data: Optional[Dict[str, Any]] = None
    ) -> List[RiskGridCell]:
        """Generate a 2D spatial risk grid for heatmap visualization."""
        cells = []
        dlat = (bounds.max_lat - bounds.min_lat) / steps_lat
        dlon = (bounds.max_lon - bounds.min_lon) / steps_lon

        for i in range(steps_lat):
            c_lat = bounds.min_lat + (i + 0.5) * dlat
            for j in range(steps_lon):
                c_lon = bounds.min_lon + (j + 0.5) * dlon
                center = GeoPoint(lat=round(c_lat, 3), lon=round(c_lon, 3))
                cell_bounds = BoundingBox(
                    min_lat=round(c_lat - dlat/2, 3),
                    max_lat=round(c_lat + dlat/2, 3),
                    min_lon=round(c_lon - dlon/2, 3),
                    max_lon=round(c_lon + dlon/2, 3)
                )
                score = self.evaluate_point(center, perception_data=perception_data, weather_data=weather_data)
                cells.append(RiskGridCell(
                    cell_id=f"GRID_{i}_{j}",
                    center=center,
                    bounds=cell_bounds,
                    risk=score
                ))
        return cells

    def explain_risk_delta(
        self,
        prev_factors: RiskFactorBreakdown,
        new_factors: RiskFactorBreakdown,
        prev_overall: float,
        new_overall: float
    ) -> RiskDeltaBreakdown:
        """
        Explain the exact point-by-point contributors to a risk score change.
        Example: 38 -> 71 (+33): +18 Sea Ice, +7 Iceberg Density, +4 Weather
        """
        delta = round(new_overall - prev_overall, 1)
        contrib: Dict[str, float] = {}

        # Sea ice change
        d_ice = round((new_factors.sea_ice_risk - prev_factors.sea_ice_risk) * self.weights["sea_ice"], 1)
        if abs(d_ice) >= 0.5:
            contrib["Sea Ice Pack"] = d_ice

        # Iceberg change
        d_berg = round((new_factors.iceberg_risk - prev_factors.iceberg_risk) * self.weights["iceberg"], 1)
        if abs(d_berg) >= 0.5:
            contrib["Iceberg Density"] = d_berg

        # Weather change
        d_weather = round((new_factors.weather_risk - prev_factors.weather_risk) * self.weights["weather"], 1)
        if abs(d_weather) >= 0.5:
            contrib["Gale Wind & Freezing Spray"] = d_weather

        # Wave change
        d_wave = round((new_factors.wave_risk - prev_factors.wave_risk) * self.weights["wave"], 1)
        if abs(d_wave) >= 0.5:
            contrib["Ocean Swell"] = d_wave

        # Glacier change
        d_glacier = round((new_factors.glacier_hazard_risk - prev_factors.glacier_hazard_risk) * self.weights["glacier_hazard"], 1)
        if abs(d_glacier) >= 0.5:
            contrib["Glacier Rift & Calving"] = d_glacier

        # Summary text
        if delta > 0:
            top_factors = ", ".join([f"{k} (+{v} pts)" for k, v in contrib.items() if v > 0])
            explanation = f"Risk increased from {prev_overall:.0f} to {new_overall:.0f} (+{delta:.0f} pts). Primary drivers: {top_factors or 'General environmental deterioration'}."
        elif delta < 0:
            top_factors = ", ".join([f"{k} ({v} pts)" for k, v in contrib.items() if v < 0])
            explanation = f"Risk decreased from {prev_overall:.0f} to {new_overall:.0f} ({delta:.0f} pts). Key improvements: {top_factors or 'Favorable drift conditions'}."
        else:
            explanation = f"Risk remained steady at {new_overall:.0f}/100. Environmental equilibrium maintained."

        return RiskDeltaBreakdown(
            previous_score=prev_overall,
            current_score=new_overall,
            delta=delta,
            main_contributors=contrib,
            explanation=explanation
        )

# Global singleton
risk_engine = CentralRiskEngine()

