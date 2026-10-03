from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import requests

from kbo_park_factors.ui_smoke import assert_game_day_html

FIXTURE_DATE = "2099-07-15"
EXPECTED_GAMES = ["LG @ 삼성", "SSG @ 두산"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:3000")
    parser.add_argument("--fixture", default="tests/fixtures/game-day-artifact.json")
    parser.add_argument("--daily-root", default="data/daily-factors")
    args = parser.parse_args()

    destination = Path(args.daily_root) / f"{FIXTURE_DATE}.json"
    had_existing = destination.exists()
    backup = destination.with_suffix(".json.bak")
    if had_existing:
        destination.replace(backup)

    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.fixture, destination)
        response = requests.get(f"{args.base_url}/", params={"date": FIXTURE_DATE}, timeout=10)
        response.raise_for_status()
        assert_game_day_html(response.text, expected_games=EXPECTED_GAMES, expected_rows=len(EXPECTED_GAMES))
    finally:
        destination.unlink(missing_ok=True)
        if had_existing:
            backup.replace(destination)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
