import json

from kbo_park_factors import official_records
from kbo_park_factors.official_records import (
    OfficialGameRecord,
    compute_baseline_profiles,
    compute_baseline_factors,
    count_home_runs_from_boxscore,
    parse_game_record,
    with_updated_baseline_factors,
)


def test_parse_game_record_counts_runs_and_home_runs_from_kbo_payloads():
    game = {
        "G_ID": "20210711HHSK0",
        "G_DT": "20210711",
        "S_NM": "문학",
        "T_SCORE_CN": "2",
        "B_SCORE_CN": "8",
    }
    scoreboard = {"T_SCORE_CN": 2, "B_SCORE_CN": 8}
    boxscore = {
        "tableEtc": json.dumps(
            {
                "rows": [
                    {"row": [{"Text": "결승타"}, {"Text": "김성현(6회 1사 만루서 좌월 홈런)"}]},
                    {"row": [{"Text": "홈런"}, {"Text": "최인호2호(2회2점 폰트) 김성현4호(6회4점 윤호솔) "}]},
                ]
            },
            ensure_ascii=False,
        )
    }

    record = parse_game_record(game, scoreboard, boxscore)

    assert record.game_id == "20210711HHSK0"
    assert record.stadium_id == "incheon-ssg-landers-field"
    assert record.runs == 10
    assert record.home_runs == 2


def test_count_home_runs_from_boxscore_returns_zero_when_hr_row_is_blank():
    boxscore = {
        "tableEtc": json.dumps(
            {"rows": [{"row": [{"Text": "홈런"}, {"Text": " "}]}]},
            ensure_ascii=False,
        )
    }

    assert count_home_runs_from_boxscore(boxscore) == 0


def test_compute_baseline_factors_shrinks_stadium_rate_vs_league_rate():
    records = [
        OfficialGameRecord(game_id="g1", date="2026-01-01", stadium_id="jamsil", runs=7, home_runs=1),
        OfficialGameRecord(game_id="g2", date="2026-01-02", stadium_id="jamsil", runs=5, home_runs=1),
        OfficialGameRecord(game_id="g3", date="2026-01-03", stadium_id="daegu-lions-park", runs=9, home_runs=3),
    ]

    factors = compute_baseline_factors(records, prior_games=3)

    assert factors["jamsil"].hr_pct == -16
    assert factors["jamsil"].runs_pct == -6
    assert factors["jamsil"].xbh_pct == 0
    assert factors["jamsil"].single_pct == 0
    assert factors["daegu-lions-park"].hr_pct == 20
    assert factors["daegu-lions-park"].runs_pct == 7


def test_compute_baseline_profiles_include_raw_and_adjusted_evidence():
    records = [
        OfficialGameRecord(game_id="g1", date="2026-01-01", stadium_id="jamsil", runs=7, home_runs=1),
        OfficialGameRecord(game_id="g2", date="2026-01-02", stadium_id="jamsil", runs=5, home_runs=1),
        OfficialGameRecord(game_id="g3", date="2026-01-03", stadium_id="daegu-lions-park", runs=9, home_runs=3),
    ]

    profiles = compute_baseline_profiles(records, prior_games=3)

    assert profiles["jamsil"].games == 2
    assert profiles["jamsil"].prior_games == 3
    assert profiles["jamsil"].raw_factors.hr_pct == -40
    assert profiles["jamsil"].adjusted_factors.hr_pct == -16
    assert profiles["daegu-lions-park"].raw_factors.hr_pct == 80
    assert profiles["daegu-lions-park"].adjusted_factors.hr_pct == 20


def test_with_updated_baseline_factors_preserves_rows_without_new_data():
    rows = [
        {
            "id": "jamsil",
            "baseline_factors": {"hr_pct": -8, "xbh_pct": 3, "single_pct": 1, "runs_pct": -2},
        },
        {
            "id": "gocheok",
            "baseline_factors": {"hr_pct": 1, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0},
        },
    ]
    factors = {
        "jamsil": compute_baseline_factors(
            [
                OfficialGameRecord(game_id="g1", date="2026-01-01", stadium_id="jamsil", runs=6, home_runs=2),
                OfficialGameRecord(game_id="g2", date="2026-01-02", stadium_id="daegu-lions-park", runs=6, home_runs=1),
            ],
            prior_games=0,
        )["jamsil"]
    }

    updated = with_updated_baseline_factors(rows, factors)

    assert updated[0]["baseline_factors"] == {"hr_pct": 33, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0}
    assert updated[1]["baseline_factors"] == {"hr_pct": 1, "xbh_pct": 0, "single_pct": 0, "runs_pct": 0}


def test_fetch_official_game_records_skips_unknown_historical_stadiums(monkeypatch):
    game = {
        "LE_ID": 1,
        "SR_ID": 0,
        "SEASON_ID": 2024,
        "G_ID": "20240323LGHH0",
        "G_DT": "20240323",
        "S_NM": "한밭",
        "T_SCORE_CN": "8",
        "B_SCORE_CN": "2",
        "GAME_RESULT_CK": 1,
    }
    boxscore = {
        "code": "100",
        "tableEtc": json.dumps(
            {"rows": [{"row": [{"Text": "홈런"}, {"Text": "오지환1호(1회1점)"}]}]},
            ensure_ascii=False,
        ),
    }

    monkeypatch.setattr(official_records, "fetch_game_list", lambda _date: [game])
    monkeypatch.setattr(official_records, "fetch_boxscore", lambda _game: boxscore)

    records = official_records.fetch_official_game_records(
        official_records.datetime.strptime("2024-03-23", "%Y-%m-%d").date(),
        official_records.datetime.strptime("2024-03-23", "%Y-%m-%d").date(),
    )

    assert records == []
