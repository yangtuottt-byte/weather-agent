"""Tools that run directly inside the Agent process."""

from datetime import date

import requests


CITIES = {
    "北京": {"latitude": 39.90, "longitude": 116.40},
    "上海": {"latitude": 31.23, "longitude": 121.47},
    "广州": {"latitude": 23.13, "longitude": 113.26},
}


def get_today() -> str:
    """Return today's date on the computer running the Agent."""
    return date.today().isoformat()


def get_weather(city: str) -> str:
    """Return the current temperature for a supported city."""
    if city not in CITIES:
        return "目前只支持北京、上海和广州。"

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": CITIES[city]["latitude"],
        "longitude": CITIES[city]["longitude"],
        "current": "temperature_2m",
        "temperature_unit": "celsius",
        "timezone": "Asia/Shanghai",
    }

    response = requests.get(url, params=params, timeout=20)
    response.raise_for_status()
    data = response.json()
    temperature = data["current"]["temperature_2m"]

    return f"{city}当前气温：{temperature}摄氏度"
