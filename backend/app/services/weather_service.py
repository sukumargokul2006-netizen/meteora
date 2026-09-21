import httpx
from typing import Dict, Any, Optional
from app.core.config import settings

class WeatherService:
    """Connector for live Open-Meteo Weather & Geocoding APIs"""

    def __init__(self):
        self.base_url = settings.OPEN_METEO_BASE_URL
        self.geocoding_url = settings.OPEN_METEO_GEOCODING_URL

    async def get_forecast(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Fetch current conditions, hourly projections, and UV/wind metrics."""
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,cloud_cover,pressure_msl,wind_speed_10m,wind_gusts_10m",
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,weather_code,wind_speed_10m,uv_index",
            "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,uv_index_max",
            "timezone": "auto"
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{self.base_url}/forecast", params=params)
            resp.raise_for_status()
            return resp.json()

    async def search_location(self, query: str) -> Optional[Dict[str, Any]]:
        """Search cities and coordinates using Open-Meteo Geocoding."""
        params = {"name": query, "count": 1, "language": "en", "format": "json"}
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(f"{self.geocoding_url}/search", params=params)
            resp.raise_for_status()
            data = resp.json()
            if data.get("results") and len(data["results"]) > 0:
                return data["results"][0]
            return None

weather_service = WeatherService()
