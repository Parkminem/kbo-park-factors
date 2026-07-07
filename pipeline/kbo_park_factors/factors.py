from __future__ import annotations

from pydantic import BaseModel

from kbo_park_factors.stadiums import FactorSet, Stadium
from kbo_park_factors.weather import WeatherSnapshot


class FactorGroups(BaseModel):
    stadium_only: FactorSet
    weather_only: FactorSet
    combined: FactorSet
    explanations: list[str]


def calculate_factor_groups(stadium: Stadium, weather: WeatherSnapshot | None) -> FactorGroups:
    stadium_only = stadium.baseline_factors
    if weather is None or stadium.type == "dome":
        weather_only = FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0)
        explanation = "돔 구장이라 외부 날씨 영향 제한"
        return FactorGroups(
            stadium_only=stadium_only,
            weather_only=weather_only,
            combined=_combine(stadium_only, weather_only),
            explanations=[explanation],
        )

    hr = 0
    xbh = 0
    single = 0
    runs = 0
    explanations: list[str] = []

    if weather.temperature_c >= 28:
        hr += 4
        xbh += 1
        runs += 2
        explanations.append("따뜻한 기온이 비거리와 득점 환경을 올림")
    elif weather.temperature_c <= 12:
        hr -= 3
        xbh -= 1
        runs -= 2
        explanations.append("낮은 기온이 비거리와 득점 환경을 낮춤")

    if weather.pressure_hpa <= 1002:
        hr += 2
        runs += 1
        explanations.append("낮은 기압이 타구 비거리에 우호적")
    elif weather.pressure_hpa >= 1020:
        hr -= 2
        runs -= 1
        explanations.append("높은 기압이 타구 비거리를 누름")

    wind_alignment = _wind_alignment(stadium.orientation_deg, weather.wind_direction_deg)
    if weather.wind_speed_mps >= 3.0 and wind_alignment == "out":
        hr += 4
        xbh += 2
        runs += 2
        explanations.append("외야 방향 바람이 장타를 도움")
    elif weather.wind_speed_mps >= 3.0 and wind_alignment == "in":
        hr -= 4
        xbh -= 1
        runs -= 2
        explanations.append("홈 방향 바람이 장타를 억제")

    if weather.precipitation_probability_pct >= 50:
        hr -= 2
        single -= 1
        runs -= 1
        explanations.append("강수 가능성이 타구 질과 경기 흐름을 낮춤")

    weather_only = FactorSet(hr_pct=hr, xbh_pct=xbh, single_pct=single, runs_pct=runs)
    if not explanations:
        explanations.append("날씨 영향은 중립에 가까움")
    return FactorGroups(
        stadium_only=stadium_only,
        weather_only=weather_only,
        combined=_combine(stadium_only, weather_only),
        explanations=explanations,
    )


def _combine(stadium: FactorSet, weather: FactorSet) -> FactorSet:
    return FactorSet(
        hr_pct=stadium.hr_pct + weather.hr_pct,
        xbh_pct=stadium.xbh_pct + weather.xbh_pct,
        single_pct=stadium.single_pct + weather.single_pct,
        runs_pct=stadium.runs_pct + weather.runs_pct,
    )


def _wind_alignment(orientation_deg: int, wind_direction_deg: int) -> str:
    diff = abs((wind_direction_deg - orientation_deg + 180) % 360 - 180)
    if diff <= 45:
        return "out"
    if diff >= 135:
        return "in"
    return "cross"
