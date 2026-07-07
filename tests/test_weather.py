from kbo_park_factors.weather import fetch_open_meteo, select_nearest_hour


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


def test_fetch_open_meteo_constrains_forecast_to_game_date(monkeypatch):
    payload = {
        "hourly": {
            "time": ["2026-07-07T18:00"],
            "temperature_2m": [27.0],
            "relative_humidity_2m": [65],
            "surface_pressure": [1004],
            "precipitation_probability": [20],
            "weather_code": [1],
            "wind_speed_10m": [3.5],
            "wind_direction_10m": [210],
        }
    }
    captured = {}

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return payload

    def fake_get(url, params, timeout):
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr("kbo_park_factors.weather.requests.get", fake_get)

    snapshot = fetch_open_meteo(37.5122, 127.0719, "2026-07-07T18:30")

    assert snapshot.temperature_c == 27.0
    assert captured["params"]["start_date"] == "2026-07-07"
    assert captured["params"]["end_date"] == "2026-07-07"
