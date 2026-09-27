from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from kbo_park_factors.official_records import fetch_official_game_records
from kbo_park_factors.validation import validate_daily_artifact


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=None, help="Target date in YYYY-MM-DD format. Defaults to today in Asia/Seoul.")
    parser.add_argument("--daily-root", default="data/daily-factors")
    parser.add_argument("--output-root", default="data/validations")
    args = parser.parse_args()

    target_date = args.date or today_kst()
    artifact_path = Path(args.daily_root) / f"{target_date}.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    actual_date = date.fromisoformat(target_date)
    records = fetch_official_game_records(actual_date, actual_date)
    validation = validate_daily_artifact(artifact, records)
    payload = {
        **validation,
        "timezone": "Asia/Seoul",
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "sources": {
            "predictions": str(artifact_path),
            "actuals": "KBO official GameCenter",
        },
    }
    output = Path(args.output_root) / f"{target_date}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


def today_kst() -> str:
    return datetime.now(ZoneInfo("Asia/Seoul")).date().isoformat()


if __name__ == "__main__":
    raise SystemExit(main())
