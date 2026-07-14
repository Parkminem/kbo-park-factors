# KBO Park Factors

Public KBO park-factor site inspired by daily ballpark/weather factor pages.

## Commands

```bash
npm install
npm run dev
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[test]"
pytest
npm run update:daily
npm run validate:daily
npm run smoke:game-day
python pipeline/generate_daily_factors.py --date 2026-07-08
python pipeline/generate_stadium_baselines.py --start 2024-03-23 --end 2026-07-07
```

## Data Flow

Python pipeline writes `data/daily-factors/YYYY-MM-DD.json`.
The Next.js app reads `data/daily-factors/<date>.json` from the `date` query parameter and defaults to today in `Asia/Seoul` when no date is provided.
Run `npm run update:daily` each day to generate today's artifact and remove older daily artifacts.
Run `npm run validate:daily` after games complete to compare today's combined HR/Runs predictions with official KBO GameCenter results. Validation output is written to `data/validations/YYYY-MM-DD.json`.
With the dev server running, run `npm run smoke:game-day` to temporarily inject a fixture game-day artifact and verify the real-game UI path.

Stadium baselines can be recomputed from official KBO GameCenter data with `pipeline/generate_stadium_baselines.py`.
The baseline updater uses completed regular-season games, total runs from the official scoreboard, and home-run counts from the official box score summary.
Pass `--write` to update `data/stadiums/kbo-stadiums.json`.

## Public Scope

This project shows stadium and weather environment factors only. It does not publish betting odds, payouts, market movement, or recommendations.

## MVP Verification

```bash
pytest
npm run typecheck
npm run build
npm run update:daily
npm run validate:daily
npm run smoke:game-day
```

Open `/` to render today's daily artifact. Missing artifacts render a visible no-data state instead of crashing.
