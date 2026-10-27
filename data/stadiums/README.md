# Stadium Orientation Audit

`orientation_deg` is the initial true bearing **from home plate toward center field**, clockwise from geographic north. A weather-provider direction is the direction wind comes **from**; add 180 degrees once to obtain its travel direction before comparing it with the field bearing.

## Coordinate Re-audit: 2026-10-27

The earlier audit incorrectly treated an outline vertex at Daegu as home plate. Its old 354-degree value was not the home-to-center-field axis. All eight outdoor parks were rechecked against the actual infield layout, identifying home by the base diamond and mound rather than by the stadium outline. The newly digitized coordinates are stored alongside each park as `field_orientation` in `kbo-stadiums.json`.

These are **approximate image/map-digitized coordinates, not an official ground survey**. Seven parks use north-up imagery; Daejeon's current playing surface uses mapped infield geometry, cross-checked with the architect's completion aerial. Estimated angular reading uncertainty is about 3 degrees for imagery and 5 degrees for the mapped Daejeon axis. These are working tolerances, not statistical confidence intervals. Retrieval date does not establish imagery acquisition date. Differences of only 1-3 degrees should not be interpreted as a material physical change.

| Stadium | Previous | Recalculated | Home latitude, longitude | Center-field latitude, longitude |
| --- | ---: | ---: | --- | --- |
| Jamsil | 195 | 196 | 37.5125300, 127.0720527 | 37.5114897, 127.0716771 |
| Sajik | 166 | 169 | 35.1945398, 129.0614578 | 35.1935096, 129.0617073 |
| Daegu Samsung Lions Park | 354 | 53 | 35.8407143, 128.6810991 | 35.8413731, 128.6821935 |
| Daejeon Hanwha Life Ballpark | 109 | 110 | 36.3162350, 127.4312080 | 36.3158819, 127.4324374 |
| Changwon NC Park | 142 | 135 | 35.2228432, 128.5819003 | 35.2220785, 128.5828364 |
| Gwangju-KIA Champions Field | 56 | 57 | 35.1678775, 126.8886539 | 35.1684607, 126.8897402 |
| Suwon KT Wiz Park | 172 | 169 | 37.3002305, 127.0096913 | 37.2992127, 127.0099300 |
| Incheon SSG Landers Field | 173 | 170 | 37.4372310, 126.6932872 | 37.4362236, 126.6935071 |

All bearings are degrees clockwise from true north and rounded to a whole degree. Gocheok's roof prevents identifying its field from these aerials. Its legacy 45-degree value is **unverified and unused**: the dome has no external wind arrow or weather factor. It has no `field_orientation` evidence and is excluded from the outdoor verification contract.

## Sources And Reproduction

- Jamsil: [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer), north-up Web Mercator zoom 19 tiles.
- Sajik, Daegu, Changwon, Gwangju, Suwon and Incheon: Google Maps north-up satellite imagery, zoom 19. Each catalog entry includes a location-specific source URL. Base diamond and mound were used to distinguish home from spectator-stand notches, dugouts and on-deck circles.
- Daejeon: [mapped infield](https://www.openstreetmap.org/way/1467519894), [mapped playing surface](https://www.openstreetmap.org/way/1467519895), and [HAEAHN's 2025 completion aerial](https://www.haeahn.com/ko/project/detail.do?prjctSeq=3183). The home-circle center is approximately 36.3162350, 127.4312080; the second-base axis anchor is 36.3161250, 127.4315910. Extend that ray to the mapped center-field fence. The old neighboring stadium is not used. OSM data is attributed to OpenStreetMap contributors (ODbL).

For imagery, convert tile pixels `(x, y)` to longitude/latitude with the standard inverse Web Mercator transform. At zoom 19, the world width is `256 * 2**19` pixels. Home and center-field anchors used in the 768-pixel tile mosaics were:

| Stadium | Global pixel origin (x, y) | Home local pixel | CF local pixel |
| --- | --- | --- | --- |
| Jamsil | 114484224, 52001280 | 535, 218 | 395, 707 |
| Sajik | 115226112, 53074688 | 351, 15 | 444, 485 |
| Daegu | 115084544, 52778240 | 111, 477 | 519, 174 |
| Changwon | 115047424, 53061632 | 247, 156 | 596, 505 |
| Gwangju | 114416128, 53086208 | 255, 657 | 660, 391 |
| Suwon | 114461184, 52100864 | 325, 277 | 414, 754 |
| Incheon | 114343168, 52036608 | 377, 264 | 459, 737 |

`calculate_field_bearing()` in `pipeline/kbo_park_factors/stadiums.py` calculates the initial great-circle bearing:

```text
y = sin(delta_longitude) * cos(latitude_2)
x = cos(latitude_1) * sin(latitude_2)
    - sin(latitude_1) * cos(latitude_2) * cos(delta_longitude)
bearing = degrees(atan2(y, x)) mod 360
```

`Stadium` rejects a stored bearing that disagrees with its coordinate evidence. Tests cover cardinal directions, all outdoor catalog entries, inconsistent metadata and Daegu wind regressions. At Daegu, a wind **from 301 degrees** travels toward 121 degrees: relative to the corrected 53-degree field axis, it is a 68-degree crosswind with an outfield component, not the previous 127-degree homeward crosswind. A wind from NNW (about 338 degrees) remains a different case: its relative angle is about 105 degrees, a crosswind with a small homeward component.
