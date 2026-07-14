import json
import sys
from pathlib import Path

import generate_daily_factors
from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import FactorGroups
from kbo_park_factors.schedule import GameSchedule
from kbo_park_factors.stadiums import FactorSet, Stadium
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
                "stadium": {
                    "id": "jamsil",
                    "name_ko": "잠실야구장",
                    "city": "서울",
                    "type": "outdoor",
                    "orientation_deg": 45,
                    "baseline_evidence": {
                        "games": 228,
                        "prior_games": 150,
                        "raw_factors": {"hr_pct": -30, "xbh_pct": 0, "single_pct": 0, "runs_pct": -8},
                        "adjusted_factors": {"hr_pct": -18, "xbh_pct": 0, "single_pct": 0, "runs_pct": -5},
                    },
                },
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
    assert payload["sources"]["schedule"] == "Naver Sports schedule API"
    assert payload["sources"]["baselines"] == "KBO official GameCenter"
    assert payload["games"][0]["stadium"]["orientation_deg"] == 45
    assert payload["games"][0]["stadium"]["baseline_evidence"]["games"] == 228
    assert payload["games"][0]["stadium"]["baseline_evidence"]["raw_factors"]["hr_pct"] == -30
    assert payload["games"][0]["factors"]["combined"]["hr_pct"] == -4


def test_generate_daily_factors_preserves_missing_stadium_rows(tmp_path: Path, monkeypatch):
    output_root = tmp_path / "daily-factors"
    schedule = GameSchedule(
        game_id="2026-07-07-NC-LOTTE",
        date="2026-07-07",
        start_time_local="18:30",
        away_team="NC",
        home_team="롯데",
        stadium_id="unknown-marsballpark",
        status="scheduled",
    )
    monkeypatch.setattr(generate_daily_factors, "fetch_kbo_daily_schedule", lambda _date: [schedule])
    monkeypatch.setattr(generate_daily_factors, "load_stadium_catalog", lambda _path: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_daily_factors.py",
            "--date",
            "2026-07-07",
            "--output-root",
            str(output_root),
        ],
    )

    assert generate_daily_factors.main() == 0

    payload = json.loads((output_root / "2026-07-07.json").read_text(encoding="utf-8"))
    assert payload["warnings"] == ["stadium_missing:2026-07-07-NC-LOTTE:unknown-marsballpark"]
    game = payload["games"][0]
    assert game["data_status"] == "stadium_missing"
    assert game["weather"] is None
    assert game["stadium"]["id"] == "unknown-marsballpark"
    assert game["stadium"]["type"] == "unknown"
    assert game["factors"] == {
        "stadium_only": {"hr_pct": 0, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0},
        "weather_only": {"hr_pct": 0, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0},
        "combined": {"hr_pct": 0, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0},
    }
    assert game["explanations"] == ["구장 메타데이터가 없어 중립 기준값으로 표시"]


def test_generate_daily_factors_defaults_to_korea_today(tmp_path: Path, monkeypatch):
    output_root = tmp_path / "daily-factors"
    monkeypatch.setattr(generate_daily_factors, "today_kst", lambda: "2026-07-08")
    monkeypatch.setattr(generate_daily_factors, "fetch_kbo_daily_schedule", lambda _date: [])
    monkeypatch.setattr(generate_daily_factors, "load_stadium_catalog", lambda _path: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_daily_factors.py",
            "--output-root",
            str(output_root),
        ],
    )

    assert generate_daily_factors.main() == 0

    payload = json.loads((output_root / "2026-07-08.json").read_text(encoding="utf-8"))
    assert payload["date"] == "2026-07-08"


def test_generate_daily_factors_can_prune_other_daily_artifacts(tmp_path: Path, monkeypatch):
    output_root = tmp_path / "daily-factors"
    output_root.mkdir()
    (output_root / "2026-07-07.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(generate_daily_factors, "fetch_kbo_daily_schedule", lambda _date: [])
    monkeypatch.setattr(generate_daily_factors, "load_stadium_catalog", lambda _path: {})
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_daily_factors.py",
            "--date",
            "2026-07-08",
            "--output-root",
            str(output_root),
            "--prune-output-root",
        ],
    )

    assert generate_daily_factors.main() == 0

    assert sorted(path.name for path in output_root.glob("*.json")) == ["2026-07-08.json"]


def test_generate_daily_factors_adds_reference_rows_for_active_unused_stadiums(tmp_path: Path, monkeypatch):
    output_root = tmp_path / "daily-factors"
    schedule = GameSchedule(
        game_id="2026-07-07-SSG-DOOSAN",
        date="2026-07-07",
        start_time_local="18:30",
        away_team="SSG",
        home_team="두산",
        stadium_id="jamsil",
        status="scheduled",
    )
    catalog = {
        "jamsil": Stadium(
            id="jamsil",
            name_ko="잠실야구장",
            name_en="Jamsil Baseball Stadium",
            city="서울",
            home_teams=["두산", "LG"],
            latitude=37.5122,
            longitude=127.0719,
            type="outdoor",
            altitude_m=25,
            outfield_size="large",
            orientation_deg=45,
            baseline_factors=FactorSet(hr_pct=-33, xbh_pct=0, single_pct=0, runs_pct=-10),
        ),
        "gocheok": Stadium(
            id="gocheok",
            name_ko="고척스카이돔",
            name_en="Gocheok Sky Dome",
            city="서울",
            home_teams=["키움"],
            latitude=37.4982,
            longitude=126.8671,
            type="dome",
            altitude_m=20,
            outfield_size="neutral",
            orientation_deg=45,
            baseline_factors=FactorSet(hr_pct=-19, xbh_pct=0, single_pct=0, runs_pct=-12),
        ),
    }
    monkeypatch.setattr(generate_daily_factors, "fetch_kbo_daily_schedule", lambda _date: [schedule])
    monkeypatch.setattr(generate_daily_factors, "load_stadium_catalog", lambda _path: catalog)
    monkeypatch.setattr(generate_daily_factors, "fetch_open_meteo", lambda *_args: None)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "generate_daily_factors.py",
            "--date",
            "2026-07-07",
            "--output-root",
            str(output_root),
        ],
    )

    assert generate_daily_factors.main() == 0

    payload = json.loads((output_root / "2026-07-07.json").read_text(encoding="utf-8"))
    assert [game["stadium"]["id"] for game in payload["games"]] == ["jamsil", "gocheok"]
    assert [game["stadium"]["orientation_deg"] for game in payload["games"]] == [45, 45]
    assert payload["games"][1]["game_id"] == "2026-07-07-gocheok-REFERENCE"
    assert payload["games"][1]["away_team"] == ""
    assert payload["games"][1]["home_team"] == "고척스카이돔"
    assert payload["games"][1]["data_status"] == "stadium_reference"
    assert payload["games"][1]["explanations"] == ["해당 날짜 경기 없음 · 현행 홈구장 기준 표시"]
