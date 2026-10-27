from __future__ import annotations

import json
import math
from pathlib import Path

from pydantic import BaseModel, Field, model_validator


class FactorSet(BaseModel):
    hr_pct: int
    xbh_pct: int
    single_pct: int
    runs_pct: int


class BaselineEvidence(BaseModel):
    games: int
    prior_games: int
    raw_factors: FactorSet
    adjusted_factors: FactorSet


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class FieldOrientation(BaseModel):
    home_plate: GeoPoint
    center_field: GeoPoint
    measured_on: str
    method: str
    estimated_error_deg: float = Field(gt=0)
    source_urls: list[str] = Field(min_length=1)
    notes: str


def calculate_field_bearing(home_plate: GeoPoint, center_field: GeoPoint) -> int:
    if home_plate == center_field:
        raise ValueError("home plate and center field must be distinct")
    lat1 = math.radians(home_plate.latitude)
    lat2 = math.radians(center_field.latitude)
    delta_lon = math.radians(center_field.longitude - home_plate.longitude)
    east = math.sin(delta_lon) * math.cos(lat2)
    north = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(delta_lon)
    return round(math.degrees(math.atan2(east, north)) % 360) % 360


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
    orientation_deg: int = Field(ge=0, lt=360)
    field_orientation: FieldOrientation | None = None
    baseline_factors: FactorSet
    baseline_evidence: BaselineEvidence | None = None

    @model_validator(mode="after")
    def validate_field_orientation(self) -> Stadium:
        if self.field_orientation is not None:
            expected = calculate_field_bearing(self.field_orientation.home_plate, self.field_orientation.center_field)
            if self.orientation_deg != expected:
                raise ValueError(f"{self.id}: orientation_deg does not match home-to-center-field coordinates ({expected})")
        return self


def load_stadium_catalog(path: Path) -> dict[str, Stadium]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    catalog = {row["id"]: Stadium.model_validate(row) for row in rows}
    if len(catalog) != len(rows):
        raise ValueError("stadium catalog contains duplicate ids")
    return catalog
