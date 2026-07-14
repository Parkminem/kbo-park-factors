from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from kbo_park_factors.official_records import OfficialGameRecord


def validate_daily_artifact(artifact: dict[str, Any], records: list[OfficialGameRecord]) -> dict[str, Any]:
    actuals_by_stadium: dict[str, deque[OfficialGameRecord]] = defaultdict(deque)
    for record in records:
        actuals_by_stadium[record.stadium_id].append(record)

    games = []
    for game in artifact.get("games", []):
        if str(game.get("data_status", "")).startswith("stadium_reference"):
            continue
        factors = game["factors"]["combined"]
        actual = _pop_actual(actuals_by_stadium, str(game["stadium"]["id"]))
        games.append(
            {
                "game_id": game["game_id"],
                "matchup": {
                    "away_team": game["away_team"],
                    "home_team": game["home_team"],
                },
                "stadium": game["stadium"],
                "predicted": {
                    "hr_pct": factors["hr_pct"],
                    "runs_pct": factors["runs_pct"],
                },
                "actual": _serialize_actual(actual),
                "status": "completed" if actual is not None else "pending",
            }
        )

    completed = [game for game in games if game["actual"] is not None]
    return {
        "date": artifact["date"],
        "summary": {
            "predicted_games": len(games),
            "completed_games": len(completed),
            "pending_games": len(games) - len(completed),
            "total_home_runs": sum(game["actual"]["home_runs"] for game in completed),
            "total_runs": sum(game["actual"]["runs"] for game in completed),
            "avg_predicted_hr_pct": _average([game["predicted"]["hr_pct"] for game in games]),
            "avg_predicted_runs_pct": _average([game["predicted"]["runs_pct"] for game in games]),
        },
        "games": games,
    }


def summarize_validation_history(validations: list[dict[str, Any]], *, recent_limit: int = 7) -> dict[str, Any]:
    ordered = sorted(validations, key=lambda validation: str(validation.get("date", "")), reverse=True)
    summaries = [validation.get("summary", {}) for validation in ordered]
    predicted_games = sum(int(summary.get("predicted_games", 0)) for summary in summaries)
    completed_games = sum(int(summary.get("completed_games", 0)) for summary in summaries)
    total_home_runs = sum(int(summary.get("total_home_runs", 0)) for summary in summaries)
    total_runs = sum(int(summary.get("total_runs", 0)) for summary in summaries)

    return {
        "summary": {
            "days": len(ordered),
            "predicted_games": predicted_games,
            "completed_games": completed_games,
            "pending_games": sum(int(summary.get("pending_games", 0)) for summary in summaries),
            "total_home_runs": total_home_runs,
            "total_runs": total_runs,
            "avg_predicted_hr_pct": _weighted_average(summaries, "avg_predicted_hr_pct"),
            "avg_predicted_runs_pct": _weighted_average(summaries, "avg_predicted_runs_pct"),
            "calibration": _calibration_summary(summaries, completed_games, total_home_runs, total_runs),
        },
        "recent_days": ordered[:recent_limit],
    }


def _pop_actual(actuals_by_stadium: dict[str, deque[OfficialGameRecord]], stadium_id: str) -> OfficialGameRecord | None:
    if not actuals_by_stadium[stadium_id]:
        return None
    return actuals_by_stadium[stadium_id].popleft()


def _serialize_actual(record: OfficialGameRecord | None) -> dict[str, Any] | None:
    if record is None:
        return None
    return {
        "official_game_id": record.game_id,
        "home_runs": record.home_runs,
        "runs": record.runs,
    }


def _average(values: list[int]) -> int | None:
    if not values:
        return None
    return round(sum(values) / len(values))


def _weighted_average(summaries: list[dict[str, Any]], key: str) -> int | None:
    total_weight = 0
    weighted_sum = 0
    for summary in summaries:
        value = summary.get(key)
        weight = int(summary.get("predicted_games", 0))
        if value is None or weight == 0:
            continue
        weighted_sum += int(value) * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return round(weighted_sum / total_weight)


def _calibration_summary(
    summaries: list[dict[str, Any]],
    completed_games: int,
    total_home_runs: int,
    total_runs: int,
) -> dict[str, Any]:
    if completed_games == 0:
        return {
            "completed_days": 0,
            "baseline_home_runs_per_game": None,
            "baseline_runs_per_game": None,
            "hr_mae_pct": None,
            "runs_mae_pct": None,
        }

    baseline_home_runs_per_game = total_home_runs / completed_games
    baseline_runs_per_game = total_runs / completed_games
    completed_summaries = [summary for summary in summaries if int(summary.get("completed_games", 0)) > 0]
    return {
        "completed_days": len(completed_summaries),
        "baseline_home_runs_per_game": round(baseline_home_runs_per_game, 2),
        "baseline_runs_per_game": round(baseline_runs_per_game, 2),
        "hr_mae_pct": _calibration_mae(completed_summaries, "avg_predicted_hr_pct", "total_home_runs", baseline_home_runs_per_game),
        "runs_mae_pct": _calibration_mae(completed_summaries, "avg_predicted_runs_pct", "total_runs", baseline_runs_per_game),
    }


def _calibration_mae(
    summaries: list[dict[str, Any]],
    prediction_key: str,
    actual_total_key: str,
    baseline_per_game: float,
) -> int | None:
    if baseline_per_game <= 0:
        return None

    weighted_error = 0.0
    total_weight = 0
    for summary in summaries:
        prediction = summary.get(prediction_key)
        completed_games = int(summary.get("completed_games", 0))
        if prediction is None or completed_games == 0:
            continue
        actual_per_game = int(summary.get(actual_total_key, 0)) / completed_games
        actual_pct = ((actual_per_game / baseline_per_game) - 1) * 100
        weighted_error += abs(int(prediction) - actual_pct) * completed_games
        total_weight += completed_games

    if total_weight == 0:
        return None
    return round(weighted_error / total_weight)
