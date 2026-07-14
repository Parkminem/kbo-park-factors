from kbo_park_factors.official_records import OfficialGameRecord
from kbo_park_factors.validation import summarize_validation_history, validate_daily_artifact


def test_validate_daily_artifact_matches_completed_games_by_stadium():
    artifact = {
        "date": "2026-07-15",
        "games": [
            {
                "game_id": "2026-07-15-SSG-DOOSAN",
                "away_team": "SSG",
                "home_team": "두산",
                "data_status": "complete",
                "stadium": {"id": "jamsil", "name_ko": "잠실야구장"},
                "factors": {
                    "combined": {"hr_pct": -18, "xbh_pct": 0, "single_pct": 0, "runs_pct": -3},
                },
            },
            {
                "game_id": "2026-07-15-daegu-lions-park-REFERENCE",
                "away_team": "",
                "home_team": "대구삼성라이온즈파크",
                "data_status": "stadium_reference",
                "stadium": {"id": "daegu-lions-park", "name_ko": "대구삼성라이온즈파크"},
                "factors": {
                    "combined": {"hr_pct": 28, "xbh_pct": 0, "single_pct": 0, "runs_pct": 5},
                },
            },
        ],
    }
    records = [
        OfficialGameRecord(
            game_id="official-1",
            date="2026-07-15",
            stadium_id="jamsil",
            runs=7,
            home_runs=1,
        )
    ]

    validation = validate_daily_artifact(artifact, records)

    assert validation["summary"] == {
        "predicted_games": 1,
        "completed_games": 1,
        "pending_games": 0,
        "total_home_runs": 1,
        "total_runs": 7,
        "avg_predicted_hr_pct": -18,
        "avg_predicted_runs_pct": -3,
    }
    assert validation["games"][0]["status"] == "completed"
    assert validation["games"][0]["actual"] == {
        "official_game_id": "official-1",
        "home_runs": 1,
        "runs": 7,
    }


def test_validate_daily_artifact_marks_missing_actuals_as_pending():
    artifact = {
        "date": "2026-07-15",
        "games": [
            {
                "game_id": "2026-07-15-LG-SAMSUNG",
                "away_team": "LG",
                "home_team": "삼성",
                "data_status": "complete",
                "stadium": {"id": "daegu-lions-park", "name_ko": "대구삼성라이온즈파크"},
                "factors": {
                    "combined": {"hr_pct": 28, "xbh_pct": 0, "single_pct": 0, "runs_pct": 5},
                },
            },
        ],
    }

    validation = validate_daily_artifact(artifact, [])

    assert validation["summary"]["predicted_games"] == 1
    assert validation["summary"]["completed_games"] == 0
    assert validation["summary"]["pending_games"] == 1
    assert validation["games"][0]["status"] == "pending"
    assert validation["games"][0]["actual"] is None


def test_summarize_validation_history_uses_game_weighted_prediction_averages():
    history = summarize_validation_history(
        [
            {
                "date": "2026-07-14",
                "summary": {
                    "predicted_games": 0,
                    "completed_games": 0,
                    "pending_games": 0,
                    "total_home_runs": 0,
                    "total_runs": 0,
                    "avg_predicted_hr_pct": None,
                    "avg_predicted_runs_pct": None,
                },
            },
            {
                "date": "2026-07-15",
                "summary": {
                    "predicted_games": 2,
                    "completed_games": 2,
                    "pending_games": 0,
                    "total_home_runs": 3,
                    "total_runs": 12,
                    "avg_predicted_hr_pct": 10,
                    "avg_predicted_runs_pct": 4,
                },
            },
            {
                "date": "2026-07-16",
                "summary": {
                    "predicted_games": 1,
                    "completed_games": 0,
                    "pending_games": 1,
                    "total_home_runs": 0,
                    "total_runs": 0,
                    "avg_predicted_hr_pct": -5,
                    "avg_predicted_runs_pct": -2,
                },
            },
        ],
        recent_limit=2,
    )

    assert history["summary"] == {
        "days": 3,
        "predicted_games": 3,
        "completed_games": 2,
        "pending_games": 1,
        "total_home_runs": 3,
        "total_runs": 12,
        "avg_predicted_hr_pct": 5,
        "avg_predicted_runs_pct": 2,
        "calibration": {
            "completed_days": 1,
            "baseline_home_runs_per_game": 1.5,
            "baseline_runs_per_game": 6.0,
            "hr_mae_pct": 10,
            "runs_mae_pct": 4,
        },
    }
    assert [day["date"] for day in history["recent_days"]] == ["2026-07-16", "2026-07-15"]


def test_summarize_validation_history_calibrates_against_history_actual_rate():
    history = summarize_validation_history(
        [
            {
                "date": "2026-07-15",
                "summary": {
                    "predicted_games": 1,
                    "completed_games": 1,
                    "pending_games": 0,
                    "total_home_runs": 2,
                    "total_runs": 14,
                    "avg_predicted_hr_pct": 40,
                    "avg_predicted_runs_pct": 30,
                },
            },
            {
                "date": "2026-07-16",
                "summary": {
                    "predicted_games": 3,
                    "completed_games": 3,
                    "pending_games": 0,
                    "total_home_runs": 3,
                    "total_runs": 26,
                    "avg_predicted_hr_pct": -20,
                    "avg_predicted_runs_pct": -10,
                },
            },
        ],
    )

    assert history["summary"]["calibration"] == {
        "completed_days": 2,
        "baseline_home_runs_per_game": 1.25,
        "baseline_runs_per_game": 10.0,
        "hr_mae_pct": 5,
        "runs_mae_pct": 5,
    }
