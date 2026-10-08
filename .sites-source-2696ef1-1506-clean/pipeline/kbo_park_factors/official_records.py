from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any

import requests

from kbo_park_factors.stadiums import FactorSet

KBO_BASE_URL = "https://www.koreabaseball.com"
KBO_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": f"{KBO_BASE_URL}/Schedule/GameCenter/Main.aspx",
    "X-Requested-With": "XMLHttpRequest",
}
KBO_SESSION = requests.Session()
DEFAULT_PRIOR_GAMES = 150

KBO_STADIUM_MAP = {
    "잠실": "jamsil",
    "고척": "gocheok",
    "고척돔": "gocheok",
    "사직": "sajik",
    "대구": "daegu-lions-park",
    "대전": "hanwha-life-ballpark",
    "창원": "changwon-nc-park",
    "광주": "gwangju-kia-champions-field",
    "수원": "suwon-kt-wiz-park",
    "문학": "incheon-ssg-landers-field",
    "인천": "incheon-ssg-landers-field",
}


@dataclass(frozen=True)
class OfficialGameRecord:
    game_id: str
    date: str
    stadium_id: str
    runs: int
    home_runs: int


@dataclass(frozen=True)
class StadiumBaselineProfile:
    games: int
    raw_factors: FactorSet
    adjusted_factors: FactorSet
    prior_games: int


def fetch_game_list(game_date: date) -> list[dict[str, Any]]:
    response = _post_kbo(
        "/ws/Main.asmx/GetKboGameList",
        {
            "leId": "1",
            "srId": "0",
            "date": game_date.strftime("%Y%m%d"),
        },
    )
    return list(response.get("game", []))


def fetch_scoreboard(game: dict[str, Any]) -> dict[str, Any]:
    return _post_kbo(
        "/ws/Schedule.asmx/GetScoreBoardScroll",
        {
            "leId": str(game["LE_ID"]),
            "srId": str(game["SR_ID"]),
            "seasonId": str(game["SEASON_ID"]),
            "gameId": game["G_ID"],
        },
    )


def fetch_boxscore(game: dict[str, Any]) -> dict[str, Any]:
    return _post_kbo(
        "/ws/Schedule.asmx/GetBoxScoreScroll",
        {
            "leId": str(game["LE_ID"]),
            "srId": str(game["SR_ID"]),
            "seasonId": str(game["SEASON_ID"]),
            "gameId": game["G_ID"],
        },
    )


def fetch_official_game_records(start: date, end: date) -> list[OfficialGameRecord]:
    records: list[OfficialGameRecord] = []
    for game_date in _date_range(start, end):
        try:
            games = fetch_game_list(game_date)
        except requests.RequestException:
            continue
        for game in games:
            if not _is_completed_regular_game(game):
                continue
            try:
                boxscore = fetch_boxscore(game)
            except requests.RequestException:
                continue
            if boxscore.get("code") != "100":
                continue
            try:
                records.append(parse_game_record(game, game, boxscore))
            except ValueError:
                continue
    return records


def parse_game_record(
    game: dict[str, Any],
    scoreboard: dict[str, Any],
    boxscore: dict[str, Any],
) -> OfficialGameRecord:
    return OfficialGameRecord(
        game_id=str(game["G_ID"]),
        date=_normalize_game_date(str(game["G_DT"])),
        stadium_id=_stadium_id(str(game.get("S_NM") or scoreboard.get("S_NM") or "")),
        runs=_int(scoreboard["T_SCORE_CN"]) + _int(scoreboard["B_SCORE_CN"]),
        home_runs=count_home_runs_from_boxscore(boxscore),
    )


def count_home_runs_from_boxscore(boxscore: dict[str, Any]) -> int:
    table = json.loads(boxscore["tableEtc"])
    for row in table.get("rows", []):
        cells = row.get("row", [])
        if len(cells) < 2:
            continue
        label = str(cells[0].get("Text", "")).strip()
        value = str(cells[1].get("Text", "")).strip()
        if label == "홈런":
            return len(re.findall(r"\d+호", value))
    return 0


def compute_baseline_factors(
    records: list[OfficialGameRecord],
    *,
    prior_games: int = DEFAULT_PRIOR_GAMES,
) -> dict[str, FactorSet]:
    return {stadium_id: profile.adjusted_factors for stadium_id, profile in compute_baseline_profiles(records, prior_games=prior_games).items()}


def compute_baseline_profiles(
    records: list[OfficialGameRecord],
    *,
    prior_games: int = DEFAULT_PRIOR_GAMES,
) -> dict[str, StadiumBaselineProfile]:
    if not records:
        return {}

    league_games = len(records)
    league_hr_per_game = sum(record.home_runs for record in records) / league_games
    league_runs_per_game = sum(record.runs for record in records) / league_games

    by_stadium: dict[str, list[OfficialGameRecord]] = {}
    for record in records:
        by_stadium.setdefault(record.stadium_id, []).append(record)

    profiles: dict[str, StadiumBaselineProfile] = {}
    for stadium_id, stadium_records in by_stadium.items():
        stadium_games = len(stadium_records)
        stadium_hr_per_game = sum(record.home_runs for record in stadium_records) / stadium_games
        stadium_runs_per_game = sum(record.runs for record in stadium_records) / stadium_games
        raw_factors = FactorSet(
            hr_pct=_rate_pct(stadium_hr_per_game, league_hr_per_game),
            xbh_pct=0,
            single_pct=0,
            runs_pct=_rate_pct(stadium_runs_per_game, league_runs_per_game),
        )
        adjusted_factors = FactorSet(
            hr_pct=_shrunk_rate_pct(stadium_hr_per_game, league_hr_per_game, stadium_games, prior_games),
            xbh_pct=0,
            single_pct=0,
            runs_pct=_shrunk_rate_pct(stadium_runs_per_game, league_runs_per_game, stadium_games, prior_games),
        )
        profiles[stadium_id] = StadiumBaselineProfile(
            games=stadium_games,
            raw_factors=raw_factors,
            adjusted_factors=adjusted_factors,
            prior_games=prior_games,
        )
    return profiles


def with_updated_baseline_factors(
    stadium_rows: list[dict[str, Any]],
    factors: dict[str, FactorSet],
    profiles: dict[str, StadiumBaselineProfile] | None = None,
) -> list[dict[str, Any]]:
    updated: list[dict[str, Any]] = []
    for row in stadium_rows:
        next_row = dict(row)
        factor = factors.get(str(row["id"]))
        if factor is not None:
            next_row["baseline_factors"] = factor.model_dump()
        profile = None if profiles is None else profiles.get(str(row["id"]))
        if profile is not None:
            next_row["baseline_evidence"] = {
                "games": profile.games,
                "prior_games": profile.prior_games,
                "raw_factors": profile.raw_factors.model_dump(),
                "adjusted_factors": profile.adjusted_factors.model_dump(),
            }
        updated.append(next_row)
    return updated


def _post_kbo(path: str, data: dict[str, str]) -> dict[str, Any]:
    response = KBO_SESSION.post(f"{KBO_BASE_URL}{path}", data=data, headers=KBO_HEADERS, timeout=8)
    response.raise_for_status()
    return response.json()


def _is_completed_regular_game(game: dict[str, Any]) -> bool:
    return str(game.get("SR_ID")) == "0" and str(game.get("GAME_RESULT_CK")) == "1"


def _date_range(start: date, end: date):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _normalize_game_date(value: str) -> str:
    if "-" in value:
        return value
    return datetime.strptime(value, "%Y%m%d").date().isoformat()


def _stadium_id(name: str) -> str:
    try:
        return KBO_STADIUM_MAP[name.strip()]
    except KeyError as exc:
        raise ValueError(f"unknown KBO stadium name: {name}") from exc


def _int(value: Any) -> int:
    return int(str(value).replace(",", ""))


def _rate_pct(selected: float, baseline: float) -> int:
    if baseline == 0:
        return 0
    return round(((selected / baseline) - 1) * 100)


def _shrunk_rate_pct(selected: float, baseline: float, games: int, prior_games: int) -> int:
    raw_pct = _rate_pct(selected, baseline)
    if games <= 0:
        return 0
    if prior_games <= 0:
        return raw_pct
    return round(raw_pct * (games / (games + prior_games)))
