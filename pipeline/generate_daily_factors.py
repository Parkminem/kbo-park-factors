from __future__ import annotations

import argparse
from pathlib import Path

from kbo_park_factors.artifacts import write_daily_artifact
from kbo_park_factors.factors import calculate_factor_groups
from kbo_park_factors.schedule import fetch_kbo_daily_schedule
from kbo_park_factors.stadiums import load_stadium_catalog
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
            warnings.append(f"missing stadium metadata for {schedule.stadium_id}")
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


if __name__ == "__main__":
    raise SystemExit(main())
