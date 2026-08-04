from pathlib import Path


def test_ui_uses_same_wind_alignment_boundaries_as_factor_model():
    source = Path("app/page.tsx").read_text(encoding="utf-8")

    assert "if (diff <= 45)" in source
    assert "if (diff >= 135)" in source


def test_ui_labels_near_perpendicular_wind_with_base_direction():
    source = Path("app/page.tsx").read_text(encoding="utf-8")

    assert "const relative = ((windTo - orientation + 540) % 360) - 180" in source
    assert "Math.abs(diff - 90) <= 15" in source
    assert 'relative < 0 ? "1루→3루" : "3루→1루"' in source
    assert "횡풍 · ${crosswindDirection}" in source
