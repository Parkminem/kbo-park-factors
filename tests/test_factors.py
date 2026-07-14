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


def test_outdoor_missing_weather_keeps_stadium_baseline_and_explains_missing_data():
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

    groups = calculate_factor_groups(stadium, None)

    assert groups.weather_only == FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0)
    assert groups.combined == stadium.baseline_factors
    assert any("날씨 데이터" in explanation for explanation in groups.explanations)
    assert all("돔 구장" not in explanation for explanation in groups.explanations)


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
    assert any("따뜻한 기온" in explanation for explanation in groups.explanations)


def test_wind_direction_uses_direction_wind_blows_toward_outfield():
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
        baseline_factors=FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0),
    )
    weather = WeatherSnapshot(
        label="맑음",
        temperature_c=24.0,
        humidity_pct=62,
        pressure_hpa=1012,
        precipitation_probability_pct=5,
        weather_code=1,
        wind_speed_mps=4.0,
        wind_direction_deg=225,
    )

    groups = calculate_factor_groups(stadium, weather)

    assert groups.weather_only.hr_pct > 0
    assert any("외야 방향 바람" in explanation for explanation in groups.explanations)


def test_wind_direction_uses_direction_wind_blows_toward_home():
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
        baseline_factors=FactorSet(hr_pct=0, xbh_pct=0, single_pct=0, runs_pct=0),
    )
    weather = WeatherSnapshot(
        label="맑음",
        temperature_c=24.0,
        humidity_pct=62,
        pressure_hpa=1012,
        precipitation_probability_pct=5,
        weather_code=1,
        wind_speed_mps=4.0,
        wind_direction_deg=45,
    )

    groups = calculate_factor_groups(stadium, weather)

    assert groups.weather_only.hr_pct < 0
    assert any("홈 방향 바람" in explanation for explanation in groups.explanations)


def test_combined_effect_is_probability_ratio_not_additive_offset():
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
        label="맑음",
        temperature_c=29.4,
        humidity_pct=62,
        pressure_hpa=1001,
        precipitation_probability_pct=20,
        weather_code=1,
        wind_speed_mps=4.2,
        wind_direction_deg=225,
    )

    groups = calculate_factor_groups(stadium, weather)

    assert groups.combined.hr_pct != groups.stadium_only.hr_pct + groups.weather_only.hr_pct
    assert any("평균 환경 대비" in explanation for explanation in groups.explanations)


def test_large_outfield_reallocates_contact_toward_xbh_and_singles():
    stadium = Stadium(
        id="test-large",
        name_ko="테스트 대형 구장",
        name_en="Test Large Park",
        city="서울",
        home_teams=["테스트"],
        latitude=37.0,
        longitude=127.0,
        type="outdoor",
        altitude_m=30,
        outfield_size="large",
        orientation_deg=45,
        baseline_factors=FactorSet(hr_pct=-12, xbh_pct=8, single_pct=4, runs_pct=-3),
    )

    groups = calculate_factor_groups(stadium, None)

    assert groups.stadium_only.hr_pct < 0
    assert groups.stadium_only.xbh_pct > 0
    assert groups.stadium_only.single_pct > 0
