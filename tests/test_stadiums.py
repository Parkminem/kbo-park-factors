from pathlib import Path
import json

import pytest

from kbo_park_factors.stadiums import load_stadium_catalog


def test_load_stadium_catalog_contains_jamsil():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))

    assert "jamsil" in catalog
    assert catalog["jamsil"].name_ko == "잠실야구장"
    assert catalog["jamsil"].type == "outdoor"
    assert catalog["jamsil"].baseline_factors.hr_pct < 0


def test_load_stadium_catalog_contains_all_regular_kbo_home_parks():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))

    assert set(catalog) == {
        "jamsil",
        "gocheok",
        "sajik",
        "daegu-lions-park",
        "hanwha-life-ballpark",
        "changwon-nc-park",
        "gwangju-kia-champions-field",
        "suwon-kt-wiz-park",
        "incheon-ssg-landers-field",
    }


def test_outdoor_stadium_orientations_match_verified_field_bearings():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))

    assert {
        stadium_id: catalog[stadium_id].orientation_deg
        for stadium_id in (
            "jamsil",
            "sajik",
            "daegu-lions-park",
            "hanwha-life-ballpark",
            "changwon-nc-park",
            "gwangju-kia-champions-field",
            "suwon-kt-wiz-park",
            "incheon-ssg-landers-field",
        )
    } == {
        "jamsil": 196,
        "sajik": 169,
        "daegu-lions-park": 53,
        "hanwha-life-ballpark": 110,
        "changwon-nc-park": 135,
        "gwangju-kia-champions-field": 57,
        "suwon-kt-wiz-park": 169,
        "incheon-ssg-landers-field": 170,
    }


@pytest.mark.parametrize("destination,expected", [((1, 0), 0), ((0, 1), 90), ((-1, 0), 180), ((0, -1), 270)])
def test_field_bearing_is_clockwise_from_true_north(destination, expected):
    from kbo_park_factors.stadiums import GeoPoint, calculate_field_bearing

    assert calculate_field_bearing(
        GeoPoint(latitude=0, longitude=0),
        GeoPoint(latitude=destination[0], longitude=destination[1]),
    ) == expected


def test_outdoor_catalog_bearings_are_reproducible_from_home_and_center_field():
    from kbo_park_factors.stadiums import calculate_field_bearing

    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))
    for stadium in catalog.values():
        if stadium.type == "dome":
            assert stadium.field_orientation is None
            continue
        evidence = stadium.field_orientation
        assert evidence is not None, stadium.id
        assert evidence.source_urls
        assert calculate_field_bearing(evidence.home_plate, evidence.center_field) == stadium.orientation_deg


def test_catalog_rejects_a_bearing_that_disagrees_with_its_coordinates(tmp_path):
    rows = json.loads(Path("data/stadiums/kbo-stadiums.json").read_text())
    rows[0]["orientation_deg"] = (rows[0]["orientation_deg"] + 180) % 360
    path = tmp_path / "stadiums.json"
    path.write_text(json.dumps(rows))

    with pytest.raises(ValueError, match="orientation_deg does not match"):
        load_stadium_catalog(path)


def test_daegu_wind_alignment_uses_actual_northeast_field_axis():
    from kbo_park_factors.factors import _wind_alignment

    daegu = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))['daegu-lions-park']
    assert _wind_alignment(daegu.orientation_deg, 270) == "out"
    assert _wind_alignment(daegu.orientation_deg, 301) == "cross"
    assert _wind_alignment(daegu.orientation_deg, 338) == "cross"
    relative = (((301 + 180) % 360 - daegu.orientation_deg + 540) % 360) - 180
    assert 45 < relative < 90


def test_hanwha_ballpark_uses_current_stadium_coordinates():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))
    stadium = catalog["hanwha-life-ballpark"]

    assert stadium.latitude == 36.3163
    assert stadium.longitude == 127.4313
