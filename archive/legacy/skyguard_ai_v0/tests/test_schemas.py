from datetime import datetime

import pandas as pd
import pytest
from pydantic import ValidationError

from src.schemas import (
    CORE_OBSERVATION_FIELDS,
    AnomalyResult,
    DiagnosticResult,
    ErrorCode,
    EventType,
    ProcessedObservation,
    QCResult,
    RawObservation,
    RecoveryStatus,
    RecoverySuggestion,
    RootCause,
    RuleSeverity,
    Severity,
    WeatherVariable,
    validate_observation,
    validate_observation_dataframe,
)


def test_valid_raw_observation_accepts_canonical_fields():
    observation = RawObservation(
        station_id="AWS-01",
        timestamp="2026-01-01T12:00:00",
        temperature=31.4,
        pressure=1008.2,
        humidity=61.0,
    )

    assert observation.station_id == "AWS-01"
    assert observation.timestamp == datetime(2026, 1, 1, 12, 0)
    assert observation.original_values() == {
        "temperature": 31.4,
        "pressure": 1008.2,
        "humidity": 61.0,
    }


def test_core_sensor_fields_are_required_but_may_be_null():
    observation = RawObservation(
        station_id="AWS-01",
        timestamp="2026-01-01T12:00:00",
        temperature=None,
        pressure=1008.2,
        humidity=61.0,
    )

    assert observation.temperature is None

    with pytest.raises(ValidationError):
        RawObservation(
            station_id="AWS-01",
            timestamp="2026-01-01T12:00:00",
            pressure=1008.2,
            humidity=61.0,
        )


def test_invalid_station_id_and_timestamp_are_rejected():
    with pytest.raises(ValidationError):
        RawObservation(
            station_id="   ",
            timestamp="2026-01-01T12:00:00",
            temperature=31.4,
            pressure=1008.2,
            humidity=61.0,
        )

    with pytest.raises(ValidationError):
        RawObservation(
            station_id="AWS-01",
            timestamp="not-a-timestamp",
            temperature=31.4,
            pressure=1008.2,
            humidity=61.0,
        )


def test_invalid_data_types_are_reported_by_validation_helper():
    observation, errors = validate_observation(
        {
            "station_id": "AWS-01",
            "timestamp": "2026-01-01T12:00:00",
            "temperature": "very hot",
            "pressure": 1008.2,
            "humidity": 61.0,
        }
    )

    assert observation is None
    assert errors
    assert errors[0].code == ErrorCode.INVALID_FIELD_TYPE
    assert errors[0].field == "temperature"


def test_validate_observation_dataframe_reports_missing_columns_and_bad_rows():
    missing_column_df = pd.DataFrame(
        [
            {
                "station_id": "AWS-01",
                "timestamp": "2026-01-01T12:00:00",
                "temperature": 31.4,
                "pressure": 1008.2,
            }
        ]
    )

    missing_report = validate_observation_dataframe(missing_column_df)

    assert missing_report["is_valid"] is False
    assert missing_report["missing_columns"] == ["humidity"]

    bad_row_df = pd.DataFrame(
        [
            {
                "station_id": "AWS-01",
                "timestamp": "2026-01-01T12:00:00",
                "temperature": 31.4,
                "pressure": 1008.2,
                "humidity": 61.0,
            },
            {
                "station_id": "AWS-02",
                "timestamp": "not-a-timestamp",
                "temperature": 30.9,
                "pressure": 1009.0,
                "humidity": 62.0,
            },
        ]
    )

    bad_row_report = validate_observation_dataframe(bad_row_df)

    assert bad_row_report["is_valid"] is False
    assert bad_row_report["row_count"] == 2
    assert bad_row_report["unique_stations"] == ["AWS-01", "AWS-02"]
    assert len(bad_row_report["invalid_rows"]) == 1


def test_canonical_enums_match_documented_taxonomy():
    assert WeatherVariable.values() == ["temperature", "pressure", "humidity"]
    assert EventType.values() == ["NORMAL", "SENSOR_FAULT", "WEATHER_EVENT", "UNCERTAIN"]
    assert RootCause.values() == [
        "NONE",
        "Spike",
        "Frozen/Stuck",
        "Drift/Bias",
        "Communication/Missing",
        "UNKNOWN",
    ]
    assert Severity.values() == ["LOW", "MEDIUM", "HIGH", "UNKNOWN"]
    assert RecoveryStatus.PENDING_VALIDATION.value == "PENDING_VALIDATION"


def test_qc_anomaly_diagnostic_and_recovery_contracts():
    qc = QCResult(
        rule_id="QC-TEMP-RANGE",
        passed=False,
        severity=RuleSeverity.HIGH,
        flag="PHYSICAL_RANGE_VIOLATION",
        message="Temperature is outside configured range.",
        affected_variables=[WeatherVariable.TEMPERATURE],
        evidence={"value": 70.0},
    )
    anomaly = AnomalyResult(is_anomaly=True, score=-0.12, available=True)
    diagnosis = DiagnosticResult(
        root_cause=RootCause.SPIKE,
        severity=Severity.HIGH,
        confidence=0.87,
    )
    recovery = RecoverySuggestion(
        original_values={"temperature": 55.0},
        suggested_values={"temperature": 31.2},
        status=RecoveryStatus.PENDING_VALIDATION,
        method="neighbor_median",
        confidence=0.7,
    )

    assert qc.affected_variables == [WeatherVariable.TEMPERATURE]
    assert anomaly.score == -0.12
    assert diagnosis.root_cause == RootCause.SPIKE
    assert recovery.operator_approval_required is True


def test_processed_observation_preserves_original_values_separately():
    raw = RawObservation(
        station_id="AWS-01",
        timestamp="2026-01-01T12:00:00",
        temperature=55.0,
        pressure=1008.2,
        humidity=61.0,
    )

    processed = ProcessedObservation.from_raw(raw)

    assert processed.station_id == raw.station_id
    assert processed.observation.temperature == 55.0
    assert processed.recovery.original_values == raw.original_values()
    assert processed.recovery.suggested_values == {}


def test_core_observation_fields_are_the_documented_mvp_contract():
    assert CORE_OBSERVATION_FIELDS == [
        "station_id",
        "timestamp",
        "temperature",
        "pressure",
        "humidity",
    ]

