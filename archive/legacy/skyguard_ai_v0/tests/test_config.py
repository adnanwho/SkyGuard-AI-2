from pathlib import Path

from src.config import (
    DEFAULT_CONFIG,
    AppConfig,
    FeatureFlagConfig,
    IsolationForestConfig,
    QCConfig,
    VariableThreshold,
)
from src.schemas import WeatherVariable


def test_default_config_contains_layer_one_foundation():
    config = DEFAULT_CONFIG

    assert config.app_name == "SkyGuard AI"
    assert config.environment == "development"
    assert config.paths.project_root == Path(__file__).resolve().parents[1]
    assert WeatherVariable.TEMPERATURE in config.qc.thresholds
    assert config.feature_flags.enable_lstm is False
    assert config.feature_flags.enable_recovery is False


def test_qc_thresholds_are_canonical_and_configured():
    qc = QCConfig()

    assert set(qc.thresholds.keys()) == {
        WeatherVariable.TEMPERATURE,
        WeatherVariable.PRESSURE,
        WeatherVariable.HUMIDITY,
    }
    assert qc.thresholds[WeatherVariable.TEMPERATURE].minimum == -50.0
    assert qc.thresholds[WeatherVariable.PRESSURE].maximum == 1080.0
    assert qc.thresholds[WeatherVariable.HUMIDITY].maximum == 100.0
    assert qc.expected_interval_minutes == 10


def test_config_models_accept_explicit_overrides():
    config = AppConfig(
        environment="test",
        qc=QCConfig(
            persistence_window=3,
            thresholds={
                WeatherVariable.TEMPERATURE: VariableThreshold(
                    minimum=-40.0,
                    maximum=55.0,
                    max_step_per_10min=4.0,
                    persistence_tolerance=0.05,
                ),
                WeatherVariable.PRESSURE: VariableThreshold(
                    minimum=700.0,
                    maximum=1060.0,
                    max_step_per_10min=4.0,
                    persistence_tolerance=0.05,
                ),
                WeatherVariable.HUMIDITY: VariableThreshold(
                    minimum=5.0,
                    maximum=95.0,
                    max_step_per_10min=20.0,
                    persistence_tolerance=0.1,
                ),
            },
        ),
        isolation_forest=IsolationForestConfig(random_state=7, contamination=0.1),
        feature_flags=FeatureFlagConfig(enable_spatial=False, enable_shap=False),
    )

    assert config.environment == "test"
    assert config.qc.persistence_window == 3
    assert config.isolation_forest.random_state == 7
    assert config.feature_flags.enable_spatial is False
    assert config.feature_flags.enable_shap is False

