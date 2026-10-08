from __future__ import annotations

import re
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

NAVER_SCHEDULE_URL = "https://api-gw.sports.naver.com/schedule/games"

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

NAVER_TEAM_MAP = {
    "두산": "DOOSAN",
    "LG": "LG",
    "SSG": "SSG",
    "KIA": "KIA",
    "롯데": "LOTTE",
    "삼성": "SAMSUNG",
    "한화": "HANWHA",
    "키움": "KIWOOM",
    "KT": "KT",
    "NC": "NC",
}

STADIUM_MAP = {
    "JAMSIL": "jamsil",
    "JAMSILBASEBALLSTADIUM": "jamsil",
    "GOCHEOKSKY": "gocheok",
    "GOCHEOKSKYDOME": "gocheok",
    "GOCHEOK": "gocheok",
    "SAJIKBASEBALLSTADIUM": "sajik",
    "SAJIK": "sajik",
    "DAEGUSAMSUNGLIONSPARK": "daegu-lions-park",
    "DAEGULIONSPARK": "daegu-lions-park",
    "DAEGU": "daegu-lions-park",
    "DAEJEONHANWHALIFEBALLPARK": "hanwha-life-ballpark",
    "HANWHALIFEBALLPARK": "hanwha-life-ballpark",
    "DAEJEON": "hanwha-life-ballpark",
    "CHANGWONNCPARK": "changwon-nc-park",
    "CHANGWON": "changwon-nc-park",
    "GWANGJUKIACHAMPIONSFIELD": "gwangju-kia-champions-field",
    "KIACHAMPIONSFIELD": "gwangju-kia-champions-field",
    "GWANGJU": "gwangju-kia-champions-field",
    "SUWONKTWIZPARK": "suwon-kt-wiz-park",
    "KTWIZPARK": "suwon-kt-wiz-park",
    "SUWON": "suwon-kt-wiz-park",
    "INCHEONSSGLANDERSFIELD": "incheon-ssg-landers-field",
    "SSGLANDERSFIELD": "incheon-ssg-landers-field",
    "INCHEON": "incheon-ssg-landers-field",
}

NAVER_STADIUM_MAP = {
    "잠실": "jamsil",
    "고척": "gocheok",
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


def parse_naver_schedule_payload(payload: dict, date: str) -> list[GameSchedule]:
    games: list[GameSchedule] = []
    for game in payload.get("result", {}).get("games", []):
        if game.get("gameDate") != date or game.get("cancel") is True:
            continue
        away_team_name = str(game["awayTeamName"])
        home_team_name = str(game["homeTeamName"])
        if _is_naver_all_star_matchup(away_team_name, home_team_name):
            continue
        away_code = _naver_team_code(away_team_name)
        home_code = _naver_team_code(home_team_name)
        games.append(
            GameSchedule(
                game_id=f"{date}-{away_code}-{home_code}",
                date=date,
                start_time_local=str(game["gameDateTime"])[11:16],
                away_team=TEAM_MAP[away_code],
                home_team=TEAM_MAP[home_code],
                stadium_id=_resolve_naver_stadium_id(str(game.get("stadium", ""))),
                status=str(game.get("statusCode", "scheduled")).lower(),
            )
        )
    return games


def _extract_location(cells: list[str]) -> str:
    if len(cells) < 5:
        return ""
    return cells[-1]


def _resolve_stadium_id(location: str, compact_row: str) -> str:
    compact_location = re.sub(r"[^A-Z0-9]+", "", location.upper())
    compact_row = re.sub(r"[^A-Z0-9]+", "", compact_row.upper())
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
    try:
        games = fetch_naver_kbo_daily_schedule(date)
        if games:
            return games
    except requests.RequestException:
        pass

    year, month, day = date.split("-")
    response = requests.get(
        "https://eng.koreabaseball.com/Schedule/DailySchedule.aspx",
        params={"date": f"{month}.{day}.{year}"},
        timeout=20,
    )
    response.raise_for_status()
    return parse_daily_schedule_html(response.text, date)


def fetch_naver_kbo_daily_schedule(date: str) -> list[GameSchedule]:
    response = requests.get(
        NAVER_SCHEDULE_URL,
        params={
            "categoryId": "kbo",
            "date": date,
            "fields": "basic,schedule",
        },
        headers={
            "Origin": "https://m.sports.naver.com",
            "Referer": "https://m.sports.naver.com/",
        },
        timeout=20,
    )
    response.raise_for_status()
    return parse_naver_schedule_payload(response.json(), date)


def _naver_team_code(name: str) -> str:
    try:
        return NAVER_TEAM_MAP[name]
    except KeyError as exc:
        raise ValueError(f"unknown Naver KBO team name: {name}") from exc


def _is_naver_all_star_matchup(away_team_name: str, home_team_name: str) -> bool:
    return {away_team_name, home_team_name} == {"나눔", "드림"}


def _resolve_naver_stadium_id(name: str) -> str:
    normalized = name.strip()
    if normalized in NAVER_STADIUM_MAP:
        return NAVER_STADIUM_MAP[normalized]
    return _resolve_stadium_id(normalized, normalized)
