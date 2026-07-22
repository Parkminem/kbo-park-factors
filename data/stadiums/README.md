# Stadium Orientation Audit

`orientation_deg` is a true bearing measured clockwise from geographic north, from home plate toward center field. Weather providers report the direction wind comes from, so the pipeline adds 180 degrees before comparing the wind vector with this bearing.

The outdoor-park values below were measured on 2026-07-22 from north-up OpenStreetMap field geometry. Where the playing surface was mapped separately, the home plate and center-field axis was calculated from the foul lines or mound-to-outfield geometry. Daejeon's current ballpark was cross-checked against the [architect's aerial photograph](https://www.haeahn.com/ko/project/detail.do?prjctSeq=3183) because the mapped playing surface was incomplete.

| Stadium | Bearing | Map |
| --- | ---: | --- |
| Jamsil Baseball Stadium | 195° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=37.5122&mlon=127.0719#map=18/37.5122/127.0719) |
| Sajik Baseball Stadium | 166° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=35.1940&mlon=129.0615#map=18/35.1940/129.0615) |
| Daegu Samsung Lions Park | 345° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=35.8410&mlon=128.6816#map=18/35.8410/128.6816) |
| Daejeon Hanwha Life Ballpark | 109° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=36.3163&mlon=127.4313#map=18/36.3163/127.4313) |
| Changwon NC Park | 142° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=35.2226&mlon=128.5826#map=18/35.2226/128.5826) |
| Gwangju-KIA Champions Field | 56° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=35.1683&mlon=126.8891#map=18/35.1683/126.8891) |
| Suwon KT Wiz Park | 172° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=37.2998&mlon=127.0097#map=18/37.2998/127.0097) |
| Incheon SSG Landers Field | 173° | [OpenStreetMap](https://www.openstreetmap.org/?mlat=37.4369&mlon=126.6933#map=18/37.4369/126.6933) |

Gocheok Sky Dome remains weather-neutral, so its field bearing does not affect the factor model.
