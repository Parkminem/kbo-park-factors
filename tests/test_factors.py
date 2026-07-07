from kbo_park_factors.factors import calculate_factor_groups
from kbo_park_factors.stadiums import FactorSet, Stadium
from kbo_park_factors.weather import WeatherSnapshot


def test_dome_uses_stadium_only_for_combined_weather_effect():
    stadium = Stadium(
        id="gocheok",
        name_ko="고척스카이돔",
        name_en="Gocheok Sky Dome",
        city="서울",
        home_teams=["키움"],
        latitude=37.4982,
        longitude=126.8671,
        type="dome",
        altitude_m=20,
        outfield_size="neutral",
        orientation_deg=45,
        baseline_factors=FactorSet(hr_pct=1, xbh_pct=0, single_pct=0, runs_pct=0),
    )
    weather = WeatherSnapshot(
        label="더움",
        temperature_c=31.0,
        humidity_pct=70,
        pressure_hpa=999,
        precipitation_probability_pct=10,
        weather_code=1,
        wind_speed_mps=6.0,
        wind_direction_deg=220,
    )

    groups = calculate_factor_groups(stadium, weather)

    assert groups.weather_only.hr_pct == 0
    assert groups.combined.hr_pct == 1


def test_hot_low_pressure_outdoor_weather_boosts_hr():
    stadium = Stadium(
        id="jamsil",
        name_ko="잠실야구장",
        name_en="Jamsil Baseball Stadium",
        city="서울",
        home_teams=["두산", "LG"],
        latitude=37.5122,
        longitude=127.0719,
        type="outdoor",
        altitude_m=25,
        outfield_size="large",
        orientation_deg=45,
        baseline_factors=FactorSet(hr_pct=-8, xbh_pct=3, single_pct=1, runs_pct=-2),
    )
    weather = WeatherSnapshot(
        label="더움",
        temperature_c=31.0,
        humidity_pct=62,
        pressure_hpa=998,
        precipitation_probability_pct=5,
        weather_code=1,
        wind_speed_mps=4.0,
        wind_direction_deg=225,
    )

    groups = calculate_factor_groups(stadium, weather)

    assert groups.weather_only.hr_pct > 0
    assert groups.combined.hr_pct > stadium.baseline_factors.hr_pct
    assert "따뜻한 기온" in groups.explanations[0]
