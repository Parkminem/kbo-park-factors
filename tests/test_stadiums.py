from pathlib import Path

from kbo_park_factors.stadiums import load_stadium_catalog


def test_load_stadium_catalog_contains_jamsil():
    catalog = load_stadium_catalog(Path("data/stadiums/kbo-stadiums.json"))

    assert "jamsil" in catalog
    assert catalog["jamsil"].name_ko == "잠실야구장"
    assert catalog["jamsil"].type == "outdoor"
    assert catalog["jamsil"].baseline_factors.hr_pct < 0
