from __future__ import annotations


EMPTY_STATE_TEXT = "오늘 예정된 KBO 경기가 없습니다."


def assert_game_day_html(html: str, *, expected_games: list[str], expected_rows: int) -> None:
    if EMPTY_STATE_TEXT in html:
        raise AssertionError("game-day smoke rendered the empty state")

    row_count = html.count('class="weatherRow')
    if row_count != expected_rows:
        raise AssertionError(f"expected {expected_rows} weather rows, found {row_count}")

    evidence_count = html.count('class="evidencePanel')
    if evidence_count < expected_rows:
        raise AssertionError(f"expected at least {expected_rows} evidence panels, found {evidence_count}")

    for game in expected_games:
        if game not in html:
            raise AssertionError(f"expected game text missing from HTML: {game}")
