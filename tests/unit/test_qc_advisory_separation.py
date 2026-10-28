import pandas as pd

from src.skyguard.preprocessing.quality_control import run_quality_control


def test_large_humidity_baseline_change_is_advisory_not_hard_qc_failure():
    data = pd.DataFrame({
        "station_id": ["A"] * 5,
        "timestamp": pd.date_range("2026-01-01", periods=5, freq="3h"),
        "temperature": [24.8, 25.0, 25.2, 25.4, 25.6],
        "pressure": [1007.6, 1007.8, 1008.0, 1008.2, 1008.4],
        "humidity": [40.0, 42.0, 44.0, 46.0, 70.0],
    })
    result = run_quality_control(data)
    last = result.iloc[-1]
    assert bool(last["humidity_deviation_fail"])
    assert bool(last["advisory_signal"])
    assert not bool(last["qc_failed"])
    assert "humidity_deviation_fail" in last["advisory_flags"]
    assert "humidity_deviation_fail" not in last["qc_flags"]


def test_physical_range_failure_remains_a_hard_qc_failure():
    data = pd.DataFrame({
        "station_id": ["A"] * 2,
        "timestamp": pd.to_datetime(["2026-01-01 00:00", "2026-01-01 03:00"]),
        "temperature": [25.0, 90.0],
        "pressure": [1008.0, 1008.0],
        "humidity": [50.0, 50.0],
    })
    result = run_quality_control(data)
    assert bool(result.iloc[-1]["temperature_range_fail"])
    assert bool(result.iloc[-1]["qc_failed"])
    assert "temperature_range_fail" in result.iloc[-1]["qc_flags"]
