from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests


@dataclass(frozen=True)
class WeatherSnapshot:
    label: str
    temperature_c: float
    humidity_pct: int
    pressure_hpa: float
    precipitation_probability_pct: int
    weather_code: int
    wind_speed_mps: float
    wind_direction_deg: int


def weather_label(code: int, precipitation_probability_pct: int, temperature_c: float) -> str:
    if precipitation_probability_pct >= 50:
        return "비 가능"
    if temperature_c >= 30:
        return "더움"
    if temperature_c <= 10:
        return "쌀쌀"
    if code <= 1:
        return "맑음"
    if code <= 3:
        return "구름"
    return "흐림"


def select_nearest_hour(payload: dict[str, Any], game_time_local: str) -> WeatherSnapshot:
    hourly = payload["hourly"]
    target = datetime.fromisoformat(game_time_local)
    times = [datetime.fromisoformat(value) for value in hourly["time"]]
    index = min(range(len(times)), key=lambda idx: abs(times[idx] - target))
    temp = float(hourly["temperature_2m"][index])
    precip = int(hourly["precipitation_probability"][index])
    code = int(hourly["weather_code"][index])
    return WeatherSnapshot(
        label=weather_label(code, precip, temp),
        temperature_c=temp,
        humidity_pct=int(hourly["relative_humidity_2m"][index]),
        pressure_hpa=float(hourly["surface_pressure"][index]),
        precipitation_probability_pct=precip,
        weather_code=code,
        wind_speed_mps=float(hourly["wind_speed_10m"][index]),
        wind_direction_deg=int(hourly["wind_direction_10m"][index]),
    )


def fetch_open_meteo(latitude: float, longitude: float, game_time_local: str) -> WeatherSnapshot:
    game_date = datetime.fromisoformat(game_time_local).date().isoformat()
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": ",".join(
            [
                "temperature_2m",
                "relative_humidity_2m",
                "surface_pressure",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ]
        ),
        "timezone": "Asia/Seoul",
        "wind_speed_unit": "ms",
        "start_date": game_date,
        "end_date": game_date,
    }
    response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20)
    response.raise_for_status()
    return select_nearest_hour(response.json(), game_time_local)
