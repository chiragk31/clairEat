"""
ClairEat — External Services
Weather (Open Meteo) and location (IPInfo) for contextual AI suggestions.
"""

from typing import Any, Dict, Optional

import httpx

from app.config import get_settings
from app.core.cache import cache_manager
from app.core.logging import get_logger

logger = get_logger(__name__)


class WeatherService:
    """Fetches current weather via Open Meteo (no API key required)."""

    # WMO weather condition codes → human labels
    WMO_CODES: Dict[int, str] = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Icy fog", 51: "Light drizzle", 53: "Moderate drizzle",
        61: "Light rain", 63: "Moderate rain", 65: "Heavy rain",
        71: "Light snow", 73: "Moderate snow", 75: "Heavy snow",
        80: "Rain showers", 81: "Moderate rain showers", 95: "Thunderstorm",
    }

    def __init__(self) -> None:
        settings = get_settings()
        self._base = settings.open_meteo_base

    async def get_weather(
        self, latitude: float, longitude: float
    ) -> Optional[Dict[str, Any]]:
        """Fetch current weather for the given coordinates.

        Results cached for 6 hours per location.
        """
        cache_key = f"weather:{latitude:.2f}:{longitude:.2f}"
        cached = await cache_manager.get_external(cache_key)
        if cached:
            return cached

        url = f"{self._base}/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": "temperature_2m",
            "forecast_days": 1,
        }
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                cw = data.get("current_weather", {})
                result = {
                    "temp_c": cw.get("temperature"),
                    "condition": self.WMO_CODES.get(cw.get("weathercode", 0), "Unknown"),
                    "wind_kmh": cw.get("windspeed"),
                }
                await cache_manager.set_external(cache_key, result)
                return result
        except Exception as exc:
            logger.warning("Weather fetch failed", error=str(exc))
            return None

    async def get_weather_by_city(self, city: str) -> Optional[Dict[str, Any]]:
        """Attempt to resolve a city to coordinates via Open Meteo geocoding."""
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(
                    "https://geocoding-api.open-meteo.com/v1/search",
                    params={"name": city, "count": 1},
                )
                resp.raise_for_status()
                results = resp.json().get("results", [])
                if not results:
                    return None
                loc = results[0]
                return await self.get_weather(loc["latitude"], loc["longitude"])
        except Exception:
            return None


class LocationService:
    """Detects approximate user location from IP via IPInfo."""

    def __init__(self) -> None:
        pass

    async def get_location_from_ip(self, ip: str) -> Optional[Dict[str, str]]:
        """Return city/region/country for the given IP address.

        Results cached for 6 hours.
        """
        if ip in ("127.0.0.1", "::1", "localhost"):
            return None  # Don't look up localhost
        cache_key = f"ip:{ip}"
        cached = await cache_manager.get_external(cache_key)
        if cached:
            return cached
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(f"https://ipinfo.io/{ip}/json")
                resp.raise_for_status()
                data = resp.json()
                result = {
                    "city": data.get("city"),
                    "region": data.get("region"),
                    "country": data.get("country"),
                }
                await cache_manager.set_external(cache_key, result)
                return result
        except Exception:
            return None
