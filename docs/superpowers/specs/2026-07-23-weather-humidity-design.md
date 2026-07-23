# Weather Humidity Display

## Goal

Show the already-collected game-time relative humidity anywhere the interface
summarizes the weather used by the park-factor model.

## Design

- Add `습도 {humidity_pct}%` immediately after temperature in each outdoor
  game's weather summary.
- Add the same humidity value to the weather sentence inside `근거 보기`.
- Keep dome and missing-weather states unchanged because they do not have an
  applicable outdoor weather snapshot.
- Reuse the existing `humidity_pct` artifact field. No provider, artifact, or
  factor-model changes are required.

## Verification

- A UI contract test must fail until both humidity render paths are present.
- Run the full Python test suite, TypeScript type check, production build, and a
  responsive browser check.
