from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from kbo_park_factors.official_records import (
    compute_baseline_factors,
    compute_baseline_profiles,
    fetch_official_game_records,
    with_updated_baseline_factors,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end", required=True, help="End date in YYYY-MM-DD format")
    parser.add_argument("--stadium-catalog", default="data/stadiums/kbo-stadiums.json")
    parser.add_argument("--write", action="store_true", help="Write computed baselines back to the stadium catalog")
    args = parser.parse_args()

    start = date.fromisoformat(args.start)
    end = date.fromisoformat(args.end)
    if end < start:
        raise ValueError("--end must be on or after --start")

    records = fetch_official_game_records(start, end)
    profiles = compute_baseline_profiles(records)
    factors = compute_baseline_factors(records)

    for stadium_id, profile in sorted(profiles.items()):
        factor = profile.adjusted_factors
        print(
            f"{stadium_id}: HR {factor.hr_pct:+d}% Runs {factor.runs_pct:+d}% "
            f"(raw HR {profile.raw_factors.hr_pct:+d}% Runs {profile.raw_factors.runs_pct:+d}%, "
            f"{profile.games} games, {profile.prior_games} prior)"
        )

    if args.write:
        catalog_path = Path(args.stadium_catalog)
        rows = json.loads(catalog_path.read_text(encoding="utf-8"))
        updated_rows = with_updated_baseline_factors(rows, factors, profiles)
        catalog_path.write_text(json.dumps(updated_rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
