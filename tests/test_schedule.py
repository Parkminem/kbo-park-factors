from kbo_park_factors.schedule import parse_daily_schedule_html, parse_naver_schedule_payload


def test_parse_daily_schedule_html_extracts_game():
    html = """
    <table>
      <tr><th>DATE</th><th>TYPE</th><th>TIME</th><th>GAME</th><th>LOCATION</th></tr>
      <tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>SSG 0:0 DOOSAN</td><td>JAMSIL</td></tr>
    </table>
    """

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert games[0].away_team == "SSG"
    assert games[0].home_team == "두산"
    assert games[0].stadium_id == "jamsil"
    assert games[0].start_time_local == "18:30"


def test_parse_daily_schedule_html_deduplicates_repeated_schedule_rows():
    row = "<tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>LG 0:0 KIWOOM</td><td>GOCHEOK SKY</td></tr>"
    html = f"<table>{row}{row}</table>"

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert len(games) == 1
    assert games[0].game_id == "2026-07-07-LG-KIWOOM"


def test_parse_daily_schedule_html_maps_current_kbo_stadium_locations():
    rows = [
        ("SSG 0:0 DOOSAN", "JAMSIL", "jamsil"),
        ("LG 0:0 KIWOOM", "GOCHEOK SKY", "gocheok"),
        ("NC 0:0 LOTTE", "SAJIK", "sajik"),
        ("KIA 0:0 SAMSUNG", "DAEGU", "daegu-lions-park"),
        ("KT 0:0 HANWHA", "DAEJEON", "hanwha-life-ballpark"),
        ("DOOSAN 0:0 NC", "CHANGWON", "changwon-nc-park"),
        ("SAMSUNG 0:0 KIA", "GWANGJU", "gwangju-kia-champions-field"),
        ("HANWHA 0:0 KT", "SUWON", "suwon-kt-wiz-park"),
        ("LOTTE 0:0 SSG", "SSG LANDERS FIELD", "incheon-ssg-landers-field"),
        ("KIWOOM 0:0 SSG", "INCHEON", "incheon-ssg-landers-field"),
    ]
    html = "<table>" + "".join(
        f"<tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>{game}</td><td>{location}</td></tr>"
        for game, location, _expected in rows
    ) + "</table>"

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert [game.stadium_id for game in games] == [expected for _game, _location, expected in rows]


def test_parse_daily_schedule_html_preserves_unmapped_stadium_location():
    html = """
    <table>
      <tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>NC 0:0 LOTTE</td><td>MARS BALLPARK</td></tr>
    </table>
    """

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert len(games) == 1
    assert games[0].game_id == "2026-07-07-NC-LOTTE"
    assert games[0].stadium_id == "unknown-marsballpark"


def test_parse_daily_schedule_html_preserves_missing_stadium_location():
    html = """
    <table>
      <tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>NC 0:0 LOTTE</td></tr>
    </table>
    """

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert len(games) == 1
    assert games[0].stadium_id == "unknown-missing-location"


def test_parse_daily_schedule_html_ignores_games_from_other_dates():
    html = """
    <table>
      <tr><td>07.07(TUE)</td><td>REGULAR</td><td>18:30</td><td>SSG 0:0 DOOSAN</td><td>JAMSIL</td></tr>
      <tr><td>07.08(WED)</td><td>REGULAR</td><td>18:30</td><td>LG 0:0 KIWOOM</td><td>GOCHEOK SKY</td></tr>
    </table>
    """

    games = parse_daily_schedule_html(html, "2026-07-07")

    assert [game.game_id for game in games] == ["2026-07-07-SSG-DOOSAN"]


def test_parse_naver_schedule_payload_extracts_all_kbo_games_for_date():
    payload = {
        "result": {
            "games": [
                {
                    "gameId": "20260707NCHH02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "대전",
                    "homeTeamName": "한화",
                    "awayTeamName": "NC",
                    "statusCode": "STARTED",
                    "cancel": False,
                },
                {
                    "gameId": "20260707HTLT02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "사직",
                    "homeTeamName": "롯데",
                    "awayTeamName": "KIA",
                    "statusCode": "RESULT",
                    "cancel": False,
                },
                {
                    "gameId": "20260707LGSS02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "대구",
                    "homeTeamName": "삼성",
                    "awayTeamName": "LG",
                    "statusCode": "RESULT",
                    "cancel": False,
                },
                {
                    "gameId": "20260707SKOB02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "잠실",
                    "homeTeamName": "두산",
                    "awayTeamName": "SSG",
                    "statusCode": "RESULT",
                    "cancel": False,
                },
                {
                    "gameId": "20260707WOKT02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "수원",
                    "homeTeamName": "KT",
                    "awayTeamName": "키움",
                    "statusCode": "RESULT",
                    "cancel": False,
                },
            ]
        }
    }

    games = parse_naver_schedule_payload(payload, "2026-07-07")

    assert [game.game_id for game in games] == [
        "2026-07-07-NC-HANWHA",
        "2026-07-07-KIA-LOTTE",
        "2026-07-07-LG-SAMSUNG",
        "2026-07-07-SSG-DOOSAN",
        "2026-07-07-KIWOOM-KT",
    ]
    assert [game.stadium_id for game in games] == [
        "hanwha-life-ballpark",
        "sajik",
        "daegu-lions-park",
        "jamsil",
        "suwon-kt-wiz-park",
    ]
    assert all(game.start_time_local == "18:30" for game in games)


def test_parse_naver_schedule_payload_skips_cancelled_games():
    payload = {
        "result": {
            "games": [
                {
                    "gameId": "20260707NCHH02026",
                    "gameDate": "2026-07-07",
                    "gameDateTime": "2026-07-07T18:30:00",
                    "stadium": "대전",
                    "homeTeamName": "한화",
                    "awayTeamName": "NC",
                    "statusCode": "BEFORE",
                    "cancel": True,
                }
            ]
        }
    }

    assert parse_naver_schedule_payload(payload, "2026-07-07") == []


def test_parse_naver_schedule_payload_skips_all_star_games():
    payload = {
        "result": {
            "games": [
                {
                    "gameId": "20260711ND0002026",
                    "gameDate": "2026-07-11",
                    "gameDateTime": "2026-07-11T18:00:00",
                    "stadium": "잠실",
                    "homeTeamName": "드림",
                    "awayTeamName": "나눔",
                    "statusCode": "BEFORE",
                    "cancel": False,
                }
            ]
        }
    }

    assert parse_naver_schedule_payload(payload, "2026-07-11") == []
