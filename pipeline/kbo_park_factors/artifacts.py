from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def write_daily_artifact(
    output: Path,
    *,
    date: str,
    games: list[dict[str, Any]],
    warnings: list[str],
) -> None:
    payload = {
        "date": date,
        "timezone": "Asia/Seoul",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": {
            "schedule": "Naver Sports schedule API",
            "weather": "open-meteo",
            "stadiums": "local-catalog",
            "baselines": "KBO official GameCenter",
        },
        "warnings": warnings,
        "games": [_serialize_game(game) for game in games],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _serialize_game(game: dict[str, Any]) -> dict[str, Any]:
    weather = game["weather"]
    factors = game["factor_groups"]
    return {
        "game_id": game["game_id"],
        "start_time_local": game["start_time_local"],
        "away_team": game["away_team"],
        "home_team": game["home_team"],
        "stadium": game["stadium"],
        "weather": weather.__dict__ if weather is not None else None,
        "factors": {
            "stadium_only": factors.stadium_only.model_dump(),
            "weather_only": factors.weather_only.model_dump(),
            "combined": factors.combined.model_dump(),
        },
        "explanations": factors.explanations,
        "data_status": game["data_status"],
    }
