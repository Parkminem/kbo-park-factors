from kbo_park_factors.weather import select_nearest_hour


def test_select_nearest_hour_uses_game_hour():
    payload = {
        "hourly": {
            "time": ["2026-07-07T17:00", "2026-07-07T18:00", "2026-07-07T19:00"],
            "temperature_2m": [25.0, 27.0, 26.5],
            "relative_humidity_2m": [70, 65, 68],
            "surface_pressure": [1005, 1004, 1004],
            "precipitation_probability": [10, 20, 15],
            "weather_code": [1, 1, 2],
            "wind_speed_10m": [2.0, 3.5, 3.0],
            "wind_direction_10m": [180, 210, 220],
        }
    }

    snapshot = select_nearest_hour(payload, "2026-07-07T18:30")

    assert snapshot.temperature_c == 27.0
    assert snapshot.wind_speed_mps == 3.5
    assert snapshot.wind_direction_deg == 210
