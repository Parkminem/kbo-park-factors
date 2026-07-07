from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup


TEAM_MAP = {
    "DOOSAN": "두산",
    "LG": "LG",
    "SSG": "SSG",
    "KIA": "KIA",
    "LOTTE": "롯데",
    "SAMSUNG": "삼성",
    "HANWHA": "한화",
    "KIWOOM": "키움",
    "KT": "KT",
    "NC": "NC",
}

STADIUM_MAP = {
    "JAMSIL": "jamsil",
    "GOCHEOKSKY": "gocheok",
    "GOCHEOK": "gocheok",
}


@dataclass(frozen=True)
class GameSchedule:
    game_id: str
    date: str
    start_time_local: str
    away_team: str
    home_team: str
    stadium_id: str
    status: str


def parse_daily_schedule_html(html: str, date: str) -> list[GameSchedule]:
    soup = BeautifulSoup(html, "html.parser")
    games: list[GameSchedule] = []
    seen_game_ids: set[str] = set()
    team_pattern = "|".join(TEAM_MAP)
    _, month, day = date.split("-")
    date_token = f"{month}.{day}"
    for table_row in soup.find_all("tr"):
        cells = [" ".join(cell.stripped_strings) for cell in table_row.find_all(["td", "th"])]
        row = " ".join(table_row.stripped_strings)
        compact_row = row.replace(" ", "")
        if date_token not in compact_row:
            continue
        time_match = re.search(r"\b(\d{2}:\d{2})\b", row)
        if not time_match:
            continue
        team_matches = list(re.finditer(rf"\b({team_pattern})\b", row))
        if len(team_matches) < 2:
            continue

        away_code = team_matches[0].group(1)
        home_code = team_matches[1].group(1)
        game_id = f"{date}-{away_code}-{home_code}"
        if game_id in seen_game_ids:
            continue
        seen_game_ids.add(game_id)
        games.append(
            GameSchedule(
                game_id=game_id,
                date=date,
                start_time_local=time_match.group(1),
                away_team=TEAM_MAP[away_code],
                home_team=TEAM_MAP[home_code],
                stadium_id=_resolve_stadium_id(_extract_location(cells), compact_row),
                status="scheduled",
            )
        )
    return games


def _extract_location(cells: list[str]) -> str:
    if len(cells) < 5:
        return ""
    return cells[-1]


def _resolve_stadium_id(location: str, compact_row: str) -> str:
    compact_location = location.replace(" ", "").upper()
    compact_row = compact_row.upper()
    stadium = next(
        (code for code in STADIUM_MAP if code in compact_location or code in compact_row),
        None,
    )
    if stadium is not None:
        return STADIUM_MAP[stadium]

    normalized_location = re.sub(r"[^a-z0-9]+", "", location.lower())
    if not normalized_location:
        normalized_location = "missing-location"
    return f"unknown-{normalized_location}"


def fetch_kbo_daily_schedule(date: str) -> list[GameSchedule]:
    year, month, day = date.split("-")
    response = requests.get(
        "https://eng.koreabaseball.com/Schedule/DailySchedule.aspx",
        params={"date": f"{month}.{day}.{year}"},
        timeout=20,
    )
    response.raise_for_status()
    return parse_daily_schedule_html(response.text, date)
