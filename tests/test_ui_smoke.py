from pathlib import Path

from kbo_park_factors.ui_smoke import assert_game_day_html

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_assert_game_day_html_accepts_real_game_screen():
    html = """
    <main>
      <article class="weatherRow clearWeather">LG @ 삼성</article>
      <article class="weatherRow rainWeather">SSG @ 두산</article>
      <details class="evidencePanel"><summary>근거 보기</summary></details>
      <details class="evidencePanel"><summary>근거 보기</summary></details>
    </main>
    """

    assert_game_day_html(html, expected_games=["LG @ 삼성", "SSG @ 두산"], expected_rows=2)


def test_assert_game_day_html_rejects_empty_state():
    html = """
    <main>
      <section class="emptyState">오늘 예정된 KBO 경기가 없습니다.</section>
    </main>
    """

    try:
        assert_game_day_html(html, expected_games=["LG @ 삼성"], expected_rows=1)
    except AssertionError as exc:
        assert "empty state" in str(exc)
    else:
        raise AssertionError("smoke assertion should reject empty-state pages")


def test_public_branding_uses_unofficial_korea_baseball_name():
    page_source = (PROJECT_ROOT / "app" / "page.tsx").read_text(encoding="utf-8")
    layout_source = (PROJECT_ROOT / "app" / "layout.tsx").read_text(encoding="utf-8")

    combined_source = page_source + layout_source

    assert "Korea Baseball Park Factors" in combined_source
    assert "Unofficial analytics project. Not affiliated with or endorsed by KBO or its clubs." in page_source
    assert "KBO PARK FACTORS" not in combined_source
    assert "KBO Park Factors" not in combined_source
