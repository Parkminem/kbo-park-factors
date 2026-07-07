from __future__ import annotations

import argparse
from pathlib import Path

from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import FactorGroups, calculate_factor_groups
from kbo_park_factors.schedule import fetch_kbo_daily_schedule
from kbo_park_factors.stadiums import FactorSet, load_stadium_catalog
from kbo_park_factors.weather import fetch_open_meteo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    parser.add_argument("--output-root", default="data/daily-factors")
    args = parser.parse_args()

    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))
    warnings: list[str] = []
    games = []
    schedules = fetch_kbo_daily_schedule(args.date)
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
        game_time = f"{args.date}T{schedule.start_time_local}"
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
                },
                "weather": weather,
                "factor_groups": factors,
                "data_status": data_status,
            }
        )

    write_daily_artifact(Path(args.output_root) / f"{args.date}.json", date=args.date, games=games, warnings=warnings)
    return 0


def _neutral_factor_groups(explanation: str) -> FactorGroups:
    neutral = FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0)
    return FactorGroups(
        stadium_only=neutral,
        weather_only=neutral,
        combined=neutral,
        explanations=[explanation],
    )


if __name__ == "__main__":
    raise SystemExit(main())
