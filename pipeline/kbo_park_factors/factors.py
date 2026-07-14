from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from kbo_park_factors.stadiums import FactorSet, Stadium
from kbo_park_factors.weather import WeatherSnapshot


class FactorGroups(BaseModel):
    stadium_only: FactorSet
    weather_only: FactorSet
    combined: FactorSet
    explanations: list[str]


@dataclass(frozen=True)
class ProbabilityTotals:
    hr: float
    xbh: float
    single: float
    runs: float


@dataclass(frozen=True)
class BattedBallProfile:
    label: str
    weight: float
    hr: float
    xbh: float
    single: float
    carry_sensitivity: float
    gap_sensitivity: float
    single_sensitivity: float


_ZERO_FACTORS = FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0)

# Reference KBO batted-ball portfolio. These are not player projections; they are a
# neutral set of susceptible contact events used like BallparkPal's public hitter
# chart: calculate each contact bucket in an average environment, calculate it
# again in the selected park/weather environment, then compare the totals.
_REFERENCE_BATTED_BALLS = (
    BattedBallProfile("wall fly", 2.0, 0.42, 0.16, 0.02, 1.20, 0.70, 0.20),
    BattedBallProfile("deep gap fly", 3.0, 0.10, 0.46, 0.05, 0.85, 1.15, 0.35),
    BattedBallProfile("medium fly", 7.0, 0.015, 0.12, 0.08, 0.55, 0.85, 0.35),
    BattedBallProfile("hard line drive", 9.0, 0.005, 0.24, 0.52, 0.20, 0.75, 0.90),
    BattedBallProfile("low line drive", 11.0, 0.001, 0.08, 0.64, 0.10, 0.35, 1.00),
)
_RUN_VALUES = ProbabilityTotals(hr=1.40, xbh=0.78, single=0.47, runs=0.0)


def calculate_factor_groups(stadium: Stadium, weather: WeatherSnapshot | None) -> FactorGroups:
    stadium_only = stadium.baseline_factors
    if weather is None:
        return FactorGroups(
            stadium_only=stadium_only,
            weather_only=_ZERO_FACTORS,
            combined=stadium_only,
            explanations=["날씨 데이터가 없어 구장 기준 확률 모델만 반영"],
        )

    if stadium.type == "dome":
        explanation = "돔 구장이라 외부 날씨 영향 제한"
        return FactorGroups(
            stadium_only=stadium_only,
            weather_only=_ZERO_FACTORS,
            combined=stadium_only,
            explanations=[explanation],
        )

    weather_only, explanations = _weather_factor_set(stadium, weather)
    combined = _combine_probability_ratios(stadium_only, weather_only)
    explanations.insert(0, "평균 환경 대비 타구 결과 확률 합산으로 산출")
    return FactorGroups(
        stadium_only=stadium_only,
        weather_only=weather_only,
        combined=combined,
        explanations=explanations,
    )


def _weather_factor_set(stadium: Stadium, weather: WeatherSnapshot) -> tuple[FactorSet, list[str]]:
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
    return weather_only, explanations


def _combine_probability_ratios(stadium: FactorSet, weather: FactorSet) -> FactorSet:
    neutral = _portfolio_totals(_ZERO_FACTORS, _ZERO_FACTORS)
    selected = _portfolio_totals(stadium, weather)
    return _totals_to_factors(selected, neutral)


def _portfolio_totals(stadium: FactorSet, weather: FactorSet) -> ProbabilityTotals:
    hr = 0.0
    xbh = 0.0
    single = 0.0
    for profile in _REFERENCE_BATTED_BALLS:
        projected_hr = _project_probability(profile.hr, stadium.hr_pct, weather.hr_pct, profile.carry_sensitivity)
        projected_xbh = _project_probability(profile.xbh, stadium.xbh_pct, weather.xbh_pct, profile.gap_sensitivity)
        projected_single = _project_probability(
            profile.single,
            stadium.single_pct,
            weather.single_pct,
            profile.single_sensitivity,
        )
        hr += profile.weight * projected_hr
        xbh += profile.weight * projected_xbh
        single += profile.weight * projected_single
    runs = hr * _RUN_VALUES.hr + xbh * _RUN_VALUES.xbh + single * _RUN_VALUES.single
    return ProbabilityTotals(hr=hr, xbh=xbh, single=single, runs=runs)


def _project_probability(base: float, stadium_pct: int, weather_pct: int, sensitivity: float) -> float:
    stadium_ratio = max(0.01, 1 + (stadium_pct / 100) * sensitivity)
    weather_ratio = max(0.01, 1 + (weather_pct / 100) * sensitivity)
    return min(1.0, max(0.0, base * stadium_ratio * weather_ratio))


def _totals_to_factors(selected: ProbabilityTotals, neutral: ProbabilityTotals) -> FactorSet:
    return FactorSet(
        hr_pct=_pct_change(selected.hr, neutral.hr),
        xbh_pct=_pct_change(selected.xbh, neutral.xbh),
        single_pct=_pct_change(selected.single, neutral.single),
        runs_pct=_pct_change(selected.runs, neutral.runs),
    )


def _pct_change(selected: float, neutral: float) -> int:
    if neutral == 0:
        return 0
    return round((selected / neutral - 1) * 100)


def _wind_alignment(orientation_deg: int, wind_direction_deg: int) -> str:
    wind_toward_deg = (wind_direction_deg + 180) % 360
    diff = abs((wind_toward_deg - orientation_deg + 180) % 360 - 180)
    if diff <= 45:
        return "out"
    if diff >= 135:
        return "in"
    return "cross"
