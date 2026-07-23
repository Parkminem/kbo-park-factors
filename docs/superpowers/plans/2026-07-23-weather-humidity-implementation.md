# Weather Humidity Display Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Display each outdoor game's game-time relative humidity in both the compact weather summary and its evidence explanation.

**Architecture:** Reuse the existing `Game.weather.humidity_pct` field already populated by Open-Meteo and bundled into daily artifacts. Keep the change inside the server-rendered `app/page.tsx` view and protect both render paths with a focused source-contract test.

**Tech Stack:** Next.js 16, React 19, TypeScript, pytest

## Global Constraints

- Render humidity as Korean UI copy: `습도 {humidity_pct}%`.
- Place humidity immediately after temperature in the compact weather summary.
- Include the same value in the expanded weather evidence sentence.
- Do not change dome or missing-weather states.
- Do not change the provider, artifact schema, or factor model.

---

### Task 1: Render Humidity In Both Weather Summaries

**Files:**
- Create: `tests/test_ui_weather_contract.py`
- Modify: `app/page.tsx:394-438`

**Interfaces:**
- Consumes: `Game.weather.humidity_pct: number`
- Produces: Server-rendered `습도 {number}%` text in `WeatherSummary` and `FactorEvidence`

- [ ] **Step 1: Write the failing source-contract test**

```python
from pathlib import Path


PAGE_SOURCE = Path("app/page.tsx").read_text(encoding="utf-8")


def test_ui_displays_humidity_in_summary_and_evidence():
    humidity_markup = "습도 {game.weather.humidity_pct}%"
    assert PAGE_SOURCE.count(humidity_markup) == 2
```

- [ ] **Step 2: Run the focused test and verify RED**

Run: `.venv/bin/python -m pytest tests/test_ui_weather_contract.py -q`

Expected: FAIL because `app/page.tsx` does not yet contain the humidity markup.

- [ ] **Step 3: Add humidity to the compact summary**

Insert this span immediately after the temperature:

```tsx
<span>습도 {game.weather.humidity_pct}%</span>
```

- [ ] **Step 4: Add humidity to the evidence sentence**

Render the weather sentence as:

```tsx
날씨는 {Math.round(game.weather.temperature_c)}도, 습도 {game.weather.humidity_pct}%,{" "}
{game.weather.precipitation_probability_pct}% rain,{" "}
{compassPoint(game.weather.wind_direction_deg)} {game.weather.wind_speed_mps.toFixed(1)} m/s를 반영합니다.
```

- [ ] **Step 5: Run the focused test and verify GREEN**

Run: `.venv/bin/python -m pytest tests/test_ui_weather_contract.py -q`

Expected: `1 passed`

- [ ] **Step 6: Run full verification**

Run:

```bash
.venv/bin/python -m pytest -q
npm run typecheck
npm run build
```

Expected: all tests pass, TypeScript reports no errors, and the production build succeeds.

- [ ] **Step 7: Verify the rendered interface**

Start the production server, inspect desktop and mobile widths, and confirm:

- Outdoor rows show temperature, humidity, precipitation, and wind without overlap.
- `근거 보기` contains the same humidity percentage.
- Dome and missing-weather rows are unchanged.

- [ ] **Step 8: Commit**

```bash
git add app/page.tsx tests/test_ui_weather_contract.py docs/superpowers/plans/2026-07-23-weather-humidity-implementation.md
git commit -m "feat: display game-time humidity"
```
