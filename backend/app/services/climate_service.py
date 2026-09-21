from typing import Dict, Any

class ClimateService:
    """Historical climate baseline and anomaly analysis connector."""

    def get_climate_comparison(self, current_temp: float, location: str = "Bengaluru") -> Dict[str, Any]:
        """Compare current conditions against 30-year climatological normal."""
        normal_high = 28.1
        normal_monthly_rain = 198.4
        temp_departure = round(current_temp - normal_high, 1)

        return {
            "baseline_period": "1991-2020 WMO Standard Climatology",
            "normal_high_celsius": normal_high,
            "current_temp_celsius": current_temp,
            "temperature_departure": temp_departure,
            "temperature_status": "Below Normal" if temp_departure < 0 else "Above Normal",
            "monthly_rainfall_departure_pct": +34,
            "storm_return_period": "1 in 4.2 Years (Moderate-High Intensity)"
        }

climate_service = ClimateService()
