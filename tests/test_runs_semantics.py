import json
from pathlib import Path

import pytest

from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import calculate_factor_groups
from kbo_park_factors.stadiums import Stadium
from kbo_park_factors.weather import WeatherSnapshot


FIXTURE = json.loads((Path(__file__).parent / "fixtures/runs-2026-10-07.json").read_text())


@pytest.mark.parametrize("row,expected_runs", list(zip(FIXTURE["games"], [-1, 2, -1])))
def test_october_7_neutral_weather_has_comparable_runs_in_serialized_groups(tmp_path, row, expected_runs):
    stadium = Stadium.model_validate(row["stadium"])
    weather = WeatherSnapshot(**row["weather"])
    groups = calculate_factor_groups(stadium, weather)
    output = tmp_path / "daily.json"
    write_daily_artifact(
        output, date=FIXTURE["date"], warnings=[], games=[{
            "game_id": stadium.id, "start_time_local": "18:30",
            "away_team": "", "home_team": "", "stadium": row["stadium"],
            "weather": weather, "factor_groups": groups, "data_status": "complete",
        }],
    )
    game = json.loads(output.read_text())["games"][0]
    assert [game["factors"][key]["runs_pct"] for key in ("stadium_only", "weather_only", "combined")] == [expected_runs, 0, expected_runs]
    # The observed run rate remains evidence, independent of portfolio Runs.
    assert game["stadium"]["baseline_evidence"] == row["stadium"]["baseline_evidence"]
    for key in ("stadium_only", "weather_only", "combined"):
        for metric in ("hr_pct", "xbh_pct", "single_pct"):
            assert game["factors"][key][metric] == row["original_factors"][key][metric]


@pytest.mark.parametrize("park_type", ["outdoor", "dome"])
def test_missing_weather_and_dome_use_portfolio_runs_without_changing_hr(park_type):
    stadium = Stadium.model_validate(FIXTURE["games"][1]["stadium"])
    stadium = stadium.model_copy(update={"type": park_type})
    weather = WeatherSnapshot(**{**FIXTURE["games"][1]["weather"], "temperature_c": 31, "pressure_hpa": 998})
    groups = calculate_factor_groups(stadium, weather if park_type == "dome" else None)
    assert groups.stadium_only.runs_pct == groups.combined.runs_pct == 2
    assert groups.weather_only.runs_pct == groups.weather_only.hr_pct == 0
    assert groups.stadium_only.hr_pct == groups.combined.hr_pct == 13
    assert stadium.baseline_factors.runs_pct == -2


def test_weather_runs_uses_contact_run_values_instead_of_independent_rules():
    stadium = Stadium.model_validate(FIXTURE["games"][0]["stadium"])
    stadium = stadium.model_copy(update={"baseline_factors": stadium.baseline_factors.model_copy(
        update={"hr_pct": 0, "xbh_pct": 0, "single_pct": 0, "runs_pct": 99}
    )})
    weather = WeatherSnapshot(**{**FIXTURE["games"][0]["weather"],
        "temperature_c": 31, "pressure_hpa": 998,
        "wind_speed_mps": 4, "wind_direction_deg": (stadium.orientation_deg + 180) % 360,
    })
    groups = calculate_factor_groups(stadium, weather)
    # Neutral run value is 12.0347; +10% HR / +3% XBH rules add
    # 0.2905192 run value: round(100 * 0.2905192 / 12.0347) == 2.
    assert groups.stadium_only.runs_pct == 0
    assert groups.weather_only.runs_pct == groups.combined.runs_pct == 2
    assert groups.weather_only.hr_pct == groups.combined.hr_pct == 10
    assert groups.weather_only.xbh_pct == 3
    assert groups.combined.xbh_pct == 2
