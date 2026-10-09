from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import FactorGroups, calculate_factor_groups
from kbo_park_factors.schedule import fetch_kbo_daily_schedule
from kbo_park_factors.stadiums import FactorSet, Stadium, load_stadium_catalog
from kbo_park_factors.weather import fetch_open_meteo

REFERENCE_START_TIME = "18:30"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Target date in YYYY-MM-DD format. Defaults to today in Asia/Seoul.")
    parser.add_argument("--output-root", default="data/daily-factors")
    parser.add_argument("--prune-output-root", action="store_true", help="Delete other daily JSON artifacts from the output root.")
    args = parser.parse_args()

    target_date = args.date or today_kst()
    output_root = Path(args.output_root)
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))
    warnings: list[str] = []
    games = []
    schedules = fetch_kbo_daily_schedule(target_date)
    used_stadium_ids: set[str] = set()
    for schedule in schedules:
        stadium = catalog.get(schedule.stadium_id)
        if stadium is None:
            warnings.append(f"stadium_missing:{schedule.game_id}:{schedule.stadium_id}")
            games.append(
                {
                    "game_id": schedule.game_id,
                    "start_time_local": schedule.start_time_local,
                    "away_team": schedule.away_team,
                    "home_team": schedule.home_team,
                    "stadium": {
                        "id": schedule.stadium_id,
                        "name_ko": "구장 정보 없음",
                        "city": None,
                        "type": "unknown",
                    },
                    "weather": None,
                    "factor_groups": _neutral_factor_groups("구장 메타데이터가 없어 중립 기준값으로 표시"),
                    "data_status": "stadium_missing",
                }
            )
            continue
        used_stadium_ids.add(stadium.id)
        game_time = f"{target_date}T{schedule.start_time_local}"
        weather = None
        data_status = "complete"
        try:
            weather = fetch_open_meteo(stadium.latitude, stadium.longitude, game_time)
        except Exception as exc:
            warnings.append(f"weather_missing:{schedule.game_id}:{exc}")
            data_status = "weather_missing"
        factors = calculate_factor_groups(stadium, weather)
        games.append(
            {
                "game_id": schedule.game_id,
                "start_time_local": schedule.start_time_local,
                "away_team": schedule.away_team,
                "home_team": schedule.home_team,
                "stadium": {
                    "id": stadium.id,
                    "name_ko": stadium.name_ko,
                    "city": stadium.city,
                    "type": stadium.type,
                    "orientation_deg": stadium.orientation_deg,
                    "baseline_evidence": stadium.baseline_evidence.model_dump() if stadium.baseline_evidence else None,
                },
                "weather": weather,
                "factor_groups": factors,
                "data_status": data_status,
            }
        )

    for stadium in catalog.values():
        if not _is_active_home_stadium(stadium) or stadium.id in used_stadium_ids:
            continue
        games.append(_reference_stadium_row(target_date, stadium, warnings))

    output = output_root / f"{target_date}.json"
    write_daily_artifact(output, date=target_date, games=games, warnings=warnings)
    if args.prune_output_root:
        prune_output_root(output_root, keep=output.name)
    return 0


def today_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


def prune_output_root(output_root: Path, *, keep: str) -> None:
    for artifact in output_root.glob("*.json"):
        if artifact.name != keep:
            artifact.unlink()


def _neutral_factor_groups(explanation: str) -> FactorGroups:
    neutral = FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0)
    return FactorGroups(
        stadium_only=neutral,
        weather_only=neutral,
        combined=neutral,
        explanations=[explanation],
    )


def _reference_stadium_row(date: str, stadium: Stadium, warnings: list[str]) -> dict:
    weather = None
    data_status = "stadium_reference"
    if stadium.type != "dome":
        try:
            weather = fetch_open_meteo(stadium.latitude, stadium.longitude, f"{date}T{REFERENCE_START_TIME}")
        except Exception as exc:
            warnings.append(f"weather_missing:{date}-{stadium.id}-REFERENCE:{exc}")
            data_status = "stadium_reference_weather_missing"

    factors = calculate_factor_groups(stadium, weather)
    return {
        "game_id": f"{date}-{stadium.id}-REFERENCE",
        "start_time_local": REFERENCE_START_TIME,
        "away_team": "",
        "home_team": stadium.name_ko,
        "stadium": {
            "id": stadium.id,
            "name_ko": stadium.name_ko,
            "city": stadium.city,
            "type": stadium.type,
            "orientation_deg": stadium.orientation_deg,
            "baseline_evidence": stadium.baseline_evidence.model_dump() if stadium.baseline_evidence else None,
        },
        "weather": weather,
        "factor_groups": FactorGroups(
            stadium_only=factors.stadium_only,
            weather_only=factors.weather_only,
            combined=factors.combined,
            explanations=["해당 날짜 경기 없음 · 현행 홈구장 기준 표시"],
        ),
        "data_status": data_status,
    }


def _is_active_home_stadium(stadium: Stadium) -> bool:
    return stadium.type in {"outdoor", "dome"} and len(stadium.home_teams) > 0


if __name__ == "__main__":
    raise SystemExit(main())
