from pathlib import Path

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
        "jamsil": 195,
        "sajik": 166,
        "daegu-lions-park": 345,
        "hanwha-life-ballpark": 109,
        "changwon-nc-park": 142,
        "gwangju-kia-champions-field": 56,
        "suwon-kt-wiz-park": 172,
        "incheon-ssg-landers-field": 173,
    }


def test_hanwha_ballpark_uses_current_stadium_coordinates():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))
    stadium = catalog["hanwha-life-ballpark"]

    assert stadium.latitude == 36.3163
    assert stadium.longitude == 127.4313
