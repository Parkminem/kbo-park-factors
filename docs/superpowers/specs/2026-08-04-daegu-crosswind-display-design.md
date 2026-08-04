# Daegu Crosswind Display Design

## Goal

Correct Daegu Samsung Lions Park's center-field bearing and describe near-perpendicular winds as directional crosswinds.

## Decisions

- Set `daegu-lions-park.orientation_deg` to `354`, measured clockwise from true north from home plate toward center field.
- Continue converting meteorological wind-from direction to wind-toward direction by adding 180 degrees.
- Keep the existing OUT (`<= 45 degrees`) and IN (`>= 135 degrees`) boundaries.
- Within the CROSS range, treat vectors within 15 degrees of perpendicular as `횡풍` and append the lateral path:
  - negative signed angle: `1루→3루`
  - positive signed angle: `3루→1루`
- Preserve `대각 외야` and `대각 홈` for crosswinds outside the near-perpendicular band.
- Let the field diagram use the corrected bearing so the current Daegu arrow rotates from about `-81 degrees` to `-90 degrees`.

## Verification

- Add regression contracts for the corrected bearing and directional crosswind copy.
- Regenerate the daily artifact, run the full Python suite, TypeScript checks, and production build.
- Compare the Daegu card before and after at the same viewport and confirm no mobile overflow.
