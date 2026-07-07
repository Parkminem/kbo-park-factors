import json
from pathlib import Path

from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import FactorGroups
from kbo_park_factors.stadiums import FactorSet
from kbo_park_factors.weather import WeatherSnapshot


def test_write_daily_artifact(tmp_path: Path):
    output = tmp_path / "2026-07-07.json"
    write_daily_artifact(
        output,
        date="2026-07-07",
        games=[
            {
                "game_id": "2026-07-07-SSG-DOO",
                "start_time_local": "18:30",
                "away_team": "SSG",
                "home_team": "두산",
                "stadium": {"id": "jamsil", "name_ko": "잠실야구장", "city": "서울", "type": "outdoor"},
                "weather": WeatherSnapshot(
                    label="맑음",
                    temperature_c=27.0,
                    humidity_pct=65,
                    pressure_hpa=1004,
                    precipitation_probability_pct=20,
                    weather_code=1,
                    wind_speed_mps=3.5,
                    wind_direction_deg=210,
                ),
                "factor_groups": FactorGroups(
                    stadium_only=FactorSet(hr_pct=-8, xbh_pct=3, single_pct=1, runs_pct=-2),
                    weather_only=FactorSet(hr_pct=4, xbh_pct=1, single_pct=0, runs_pct=2),
                    combined=FactorSet(hr_pct=-4, xbh_pct=4, single_pct=1, runs_pct=0),
                    explanations=["따뜻한 기온이 비거리와 득점 환경을 올림"],
                ),
                "data_status": "complete",
            }
        ],
        warnings=[],
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["date"] == "2026-07-07"
    assert payload["games"][0]["factors"]["combined"]["hr_pct"] == -4
