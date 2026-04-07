"""Weather service: real-time weather data using OpenWeatherMap."""

import logging
from typing import Any, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class WeatherService:
    """Fetch current weather and forecasts from OpenWeatherMap API."""

    BASE_URL = "https://api.openweathermap.org/data/2.5"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENWEATHER_API_KEY

    async def get_current_weather(self, city: str, units: str = "metric") -> Dict[str, Any]:
        """Fetch current weather for a city."""
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured.", "success": False}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/weather",
                    params={"q": city, "units": units, "appid": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "success": True,
                    "city": data.get("name"),
                    "country": data.get("sys", {}).get("country"),
                    "temperature": data.get("main", {}).get("temp"),
                    "feels_like": data.get("main", {}).get("feels_like"),
                    "humidity": data.get("main", {}).get("humidity"),
                    "description": data.get("weather", [{}])[0].get("description"),
                    "icon": data.get("weather", [{}])[0].get("icon"),
                    "wind_speed": data.get("wind", {}).get("speed"),
                    "visibility": data.get("visibility"),
                    "units": units,
                }
        except httpx.HTTPStatusError as exc:
            logger.error("Weather API error: %s", exc)
            return {"success": False, "error": f"Weather API error: {exc.response.status_code}"}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Weather fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}

    async def get_forecast(self, city: str, days: int = 5, units: str = "metric") -> Dict[str, Any]:
        """Fetch 5-day weather forecast."""
        if not self.api_key:
            return {"error": "OpenWeatherMap API key not configured.", "success": False}
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{self.BASE_URL}/forecast",
                    params={"q": city, "units": units, "cnt": days * 8, "appid": self.api_key},
                )
                resp.raise_for_status()
                data = resp.json()
                forecasts = [
                    {
                        "datetime": item.get("dt_txt"),
                        "temp": item.get("main", {}).get("temp"),
                        "description": item.get("weather", [{}])[0].get("description"),
                        "humidity": item.get("main", {}).get("humidity"),
                        "wind_speed": item.get("wind", {}).get("speed"),
                    }
                    for item in data.get("list", [])
                ]
                return {"success": True, "city": city, "forecasts": forecasts, "units": units}
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Forecast fetch failed: %s", exc)
            return {"success": False, "error": str(exc)}
