from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class FactorSet(BaseModel):
    hr_pct: int
    xbh_pct: int
    single_pct: int
    runs_pct: int


class Stadium(BaseModel):
    id: str
    name_ko: str
    name_en: str
    city: str
    home_teams: list[str]
    latitude: float
    longitude: float
    type: str = Field(pattern="^(outdoor|dome)$")
    altitude_m: int
    outfield_size: str
    orientation_deg: int
    baseline_factors: FactorSet


def load_stadium_catalog(path: Path) -> dict[str, Stadium]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    catalog = {row["id"]: Stadium.model_validate(row) for row in rows}
    if len(catalog) != len(rows):
        raise ValueError("stadium catalog contains duplicate ids")
    return catalog
