from kbo_park_factors.schedule import parse_daily_schedule_html


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
