from pathlib import Path


PAGE_SOURCE = Path("app/page.tsx").read_text(encoding="utf-8")


def test_ui_displays_humidity_in_summary_and_evidence():
    humidity_markup = "습도 {game.weather.humidity_pct}%"
    assert PAGE_SOURCE.count(humidity_markup) == 2
