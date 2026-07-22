from pathlib import Path


def test_ui_uses_same_wind_alignment_boundaries_as_factor_model():
    source = Path("app/page.tsx").read_text(encoding="utf-8")

    assert "if (diff <= 45)" in source
    assert "if (diff >= 135)" in source
