"""
Canonical SkyGuard AI data contracts.

Layer 1 owns schema and validation only. Physics/QC, preprocessing,
feature engineering, ML, and dashboard behavior are implemented in later
layers against these contracts.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator


SCHEMA_VERSION = "1.0.0"

CORE_OBSERVATION_FIELDS = [
    "station_id",
    "timestamp",
    "temperature",
    "pressure",
    "humidity",
]

OPTIONAL_METADATA_FIELDS = [
    "latitude",
    "longitude",
    "elevation",
]

RAW_OBSERVATION_COLUMNS = CORE_OBSERVATION_FIELDS + OPTIONAL_METADATA_FIELDS

CORE_VARIABLES = [
    "temperature",
    "pressure",
    "humidity",
]


class StrEnum(str, Enum):
    """String enum with a small convenience for tests and UI choices."""

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]


class WeatherVariable(StrEnum):
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    HUMIDITY = "humidity"


class EventType(StrEnum):
    NORMAL = "NORMAL"
    SENSOR_FAULT = "SENSOR_FAULT"
    WEATHER_EVENT = "WEATHER_EVENT"
    UNCERTAIN = "UNCERTAIN"


class RootCause(StrEnum):
    NONE = "NONE"
    SPIKE = "Spike"
    FROZEN_STUCK = "Frozen/Stuck"
    DRIFT_BIAS = "Drift/Bias"
    COMMUNICATION_MISSING = "Communication/Missing"
    UNKNOWN = "UNKNOWN"


class Severity(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class HealthStatus(StrEnum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    DEGRADING = "DEGRADING"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class RecoveryStatus(StrEnum):
    NOT_AVAILABLE = "NOT_AVAILABLE"
    NOT_REQUIRED = "NOT_REQUIRED"
    SUGGESTED = "SUGGESTED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"


class RuleSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    UNKNOWN = "UNKNOWN"


class ErrorCode(StrEnum):
    MISSING_REQUIRED_FIELD = "MISSING_REQUIRED_FIELD"
    INVALID_FIELD_TYPE = "INVALID_FIELD_TYPE"
    INVALID_FIELD_VALUE = "INVALID_FIELD_VALUE"
    SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"


class SkyGuardBaseModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=False,
    )


class SchemaError(SkyGuardBaseModel):
    code: ErrorCode
    message: str
    field: str | None = None
    recoverable: bool = True


class StationMetadata(SkyGuardBaseModel):
    station_id: str = Field(..., min_length=1)
    name: str | None = None
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    elevation: float | None = Field(default=None, ge=-500.0, le=9000.0)
    region: str | None = None
    is_active: bool = True

    @field_validator("station_id")
    @classmethod
    def station_id_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("station_id must not be blank")
        return value


class RawObservation(SkyGuardBaseModel):
    station_id: str = Field(..., min_length=1)
    timestamp: datetime
    temperature: float | None = Field(..., description="Air temperature in Celsius")
    pressure: float | None = Field(..., description="Atmospheric pressure in hPa")
    humidity: float | None = Field(..., description="Relative humidity in percent")
    latitude: float | None = Field(default=None, ge=-90.0, le=90.0)
    longitude: float | None = Field(default=None, ge=-180.0, le=180.0)
    elevation: float | None = Field(default=None, ge=-500.0, le=9000.0)

    @field_validator("station_id")
    @classmethod
    def station_id_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("station_id must not be blank")
        return value

    def original_values(self) -> dict[str, float | None]:
        return {
            "temperature": self.temperature,
            "pressure": self.pressure,
            "humidity": self.humidity,
        }


class QCResult(SkyGuardBaseModel):
    rule_id: str = Field(..., min_length=1)
    passed: bool
    severity: RuleSeverity = RuleSeverity.INFO
    flag: str | None = None
    message: str
    affected_variables: list[WeatherVariable] = Field(default_factory=list)
    evidence: dict[str, Any] = Field(default_factory=dict)


class QualityResult(SkyGuardBaseModel):
    is_valid: bool = True
    rules: list[QCResult] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AnomalyResult(SkyGuardBaseModel):
    is_anomaly: bool = False
    score: float | None = None
    model_version: str | None = None
    available: bool = False
    evidence: dict[str, Any] = Field(default_factory=dict)


class ContextResult(SkyGuardBaseModel):
    event_type: EventType = EventType.UNCERTAIN
    temporal_evidence: dict[str, Any] = Field(default_factory=dict)
    spatial_evidence: dict[str, Any] = Field(default_factory=dict)


class DiagnosticResult(SkyGuardBaseModel):
    root_cause: RootCause = RootCause.UNKNOWN
    severity: Severity = Severity.UNKNOWN
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    evidence: dict[str, Any] = Field(default_factory=dict)


class ExplanationResult(SkyGuardBaseModel):
    available: bool = False
    feature_contributions: dict[str, float] = Field(default_factory=dict)
    plain_language: str = "Explanation is unavailable for this processing mode."


class HealthResult(SkyGuardBaseModel):
    score: float | None = Field(default=None, ge=0.0, le=100.0)
    status: HealthStatus = HealthStatus.UNKNOWN
    trend: str | None = None


class MaintenanceRecommendation(SkyGuardBaseModel):
    recommendation: str | None = None
    evidence: dict[str, Any] = Field(default_factory=dict)


class RecoverySuggestion(SkyGuardBaseModel):
    original_values: dict[str, float | None] = Field(default_factory=dict)
    suggested_values: dict[str, float | None] = Field(default_factory=dict)
    status: RecoveryStatus = RecoveryStatus.NOT_AVAILABLE
    method: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str | None = None
    operator_approval_required: bool = True


class ProcessedObservation(SkyGuardBaseModel):
    schema_version: str = SCHEMA_VERSION
    station_id: str
    timestamp: datetime
    observation: RawObservation
    quality: QualityResult = Field(default_factory=QualityResult)
    features: dict[str, Any] = Field(default_factory=dict)
    anomaly: AnomalyResult = Field(default_factory=AnomalyResult)
    context: ContextResult = Field(default_factory=ContextResult)
    diagnosis: DiagnosticResult = Field(default_factory=DiagnosticResult)
    explanation: ExplanationResult = Field(default_factory=ExplanationResult)
    health: HealthResult = Field(default_factory=HealthResult)
    maintenance: MaintenanceRecommendation = Field(default_factory=MaintenanceRecommendation)
    recovery: RecoverySuggestion = Field(default_factory=RecoverySuggestion)
    errors: list[SchemaError] = Field(default_factory=list)
    latency_ms: dict[str, float] = Field(default_factory=dict)

    @classmethod
    def from_raw(cls, observation: RawObservation, **overrides: Any) -> "ProcessedObservation":
        recovery = overrides.pop("recovery", None)
        if recovery is None:
            recovery = RecoverySuggestion(original_values=observation.original_values())
        return cls(
            station_id=observation.station_id,
            timestamp=observation.timestamp,
            observation=observation,
            recovery=recovery,
            **overrides,
        )


def validation_error_to_schema_errors(error: ValidationError) -> list[SchemaError]:
    schema_errors: list[SchemaError] = []
    for item in error.errors():
        field = ".".join(str(part) for part in item.get("loc", [])) or None
        error_type = item.get("type", "")
        if "missing" in error_type:
            code = ErrorCode.MISSING_REQUIRED_FIELD
        elif "float" in error_type or "datetime" in error_type or "string" in error_type:
            code = ErrorCode.INVALID_FIELD_TYPE
        elif "greater_than" in error_type or "less_than" in error_type:
            code = ErrorCode.INVALID_FIELD_VALUE
        else:
            code = ErrorCode.SCHEMA_VALIDATION_ERROR
        schema_errors.append(
            SchemaError(
                code=code,
                message=str(item.get("msg", "Schema validation failed.")),
                field=field,
                recoverable=True,
            )
        )
    return schema_errors


def validate_observation(data: dict[str, Any]) -> tuple[RawObservation | None, list[SchemaError]]:
    try:
        return RawObservation.model_validate(data), []
    except ValidationError as exc:
        return None, validation_error_to_schema_errors(exc)


def validate_observation_dataframe(df: pd.DataFrame) -> dict[str, Any]:
    report: dict[str, Any] = {
        "is_valid": True,
        "row_count": int(len(df)),
        "missing_columns": [],
        "null_counts": {},
        "invalid_rows": [],
        "unique_stations": [],
        "schema_version": SCHEMA_VERSION,
    }

    for column in CORE_OBSERVATION_FIELDS:
        if column not in df.columns:
            report["missing_columns"].append(column)
            report["is_valid"] = False

    if report["missing_columns"]:
        return report

    report["null_counts"] = {
        column: int(df[column].isna().sum())
        for column in CORE_OBSERVATION_FIELDS
        if column in df.columns
    }
    report["unique_stations"] = sorted(
        str(station)
        for station in df["station_id"].dropna().unique().tolist()
        if str(station).strip()
    )

    allowed_columns = set(RAW_OBSERVATION_COLUMNS)
    validation_columns = [column for column in df.columns if column in allowed_columns]
    for index, row in df[validation_columns].iterrows():
        payload = row.where(pd.notna(row), None).to_dict()
        _, errors = validate_observation(payload)
        if errors:
            report["invalid_rows"].append(
                {
                    "index": int(index) if isinstance(index, int) else str(index),
                    "errors": [error.model_dump(mode="json") for error in errors],
                }
            )
            report["is_valid"] = False

    return report


# Backward-compatible aliases for older placeholder code/imports. New code should
# use the canonical names above.
AnomalyType = RootCause
SensorType = WeatherVariable
WeatherTelemetryRecord = RawObservation
validate_telemetry_dataframe = validate_observation_dataframe

