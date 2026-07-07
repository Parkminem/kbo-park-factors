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
The Next.js app renders the latest available daily artifact.

## Public Scope

This project shows stadium and weather environment factors only. It does not publish betting odds, payouts, market movement, or recommendations.
