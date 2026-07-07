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
python pipeline/generate_daily_factors.py --date 2026-07-07
```

## Data Flow

Python pipeline writes `data/daily-factors/YYYY-MM-DD.json`.
The Next.js app reads `data/daily-factors/<date>.json` from the `date` query parameter and defaults to the MVP sample date, `2026-07-07`, when no date is provided.

## Public Scope

This project shows stadium and weather environment factors only. It does not publish betting odds, payouts, market movement, or recommendations.

## MVP Verification

```bash
pytest
npm run typecheck
npm run build
python pipeline/generate_daily_factors.py --date 2026-07-07
```

Open `/?date=2026-07-07` to render a specific daily artifact. Missing artifacts render a visible no-data state instead of crashing.
