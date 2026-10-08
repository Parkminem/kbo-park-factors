# Daegu Crosswind Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Correct Daegu's field orientation and show near-perpendicular wind with an explicit base-to-base direction.

**Architecture:** The stadium catalog remains the source of field bearings. The UI derives a signed wind-to angle relative to center field, keeps the factor-model OUT/IN thresholds, and adds a narrow crosswind presentation band without changing factor categories.

**Tech Stack:** Next.js, React, TypeScript, Python pytest, JSON stadium catalog

## Global Constraints

- Daegu center-field bearing is `354 degrees`.
- Near-perpendicular means within `15 degrees` of `90 degrees`.
- Meteorological wind direction remains a wind-from direction and must be converted by adding 180 degrees.

---

### Task 1: Correct Bearing And Crosswind Presentation

**Files:**
- Modify: `tests/test_stadiums.py`
- Modify: `tests/test_ui_wind_contract.py`
- Modify: `data/stadiums/kbo-stadiums.json`
- Modify: `data/stadiums/README.md`
- Modify: `app/page.tsx`
- Regenerate: `data/daily-factors/2026-08-04.json`
- Regenerate: `app/generated-data.ts`

**Interfaces:**
- Consumes: `Game.weather.wind_direction_deg` and `Game.stadium.orientation_deg`
- Produces: `windImpact(game)` with directional crosswind detail and `BallparkWind` arrow rotation from the corrected bearing

- [x] **Step 1: Write failing regression tests**

Update the Daegu expected bearing to `354` and require the UI source to contain the signed-angle, near-perpendicular, and lateral-direction rules.

- [x] **Step 2: Run focused tests to verify failure**

Run: `.venv/bin/pytest tests/test_stadiums.py tests/test_ui_wind_contract.py -q`

Expected: failures for the old `345` bearing and missing directional crosswind copy.

- [x] **Step 3: Implement the minimal correction**

Update the catalog and audit record, then calculate:

```ts
const relative = ((windTo - orientation + 540) % 360) - 180;
const diff = Math.abs(relative);
```

For `Math.abs(diff - 90) <= 15`, return `횡풍 · 1루→3루` when `relative < 0`, otherwise `횡풍 · 3루→1루`.

- [x] **Step 4: Regenerate today's artifact**

Run: `.venv/bin/python pipeline/generate_daily_factors.py --prune-output-root`

Expected: the Daegu game contains `orientation_deg: 354`.

- [x] **Step 5: Verify implementation**

Run focused tests, the full Python suite, `npm run typecheck`, and `npm run build`.

Expected: all commands exit successfully.

- [x] **Step 6: Verify the visual result**

Open the production build, capture the Daegu card, and verify it reads `CROSS` with `횡풍 · 1루→3루`, has a horizontal arrow, and fits at desktop and mobile widths.
