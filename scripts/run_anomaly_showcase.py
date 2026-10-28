"""Generate a reproducible, labelled anomaly-detection showcase without PyOD.
This is a DEMONSTRATION dataset, not live telemetry or a model-performance benchmark.
It runs scikit-learn IsolationForest and explicit sensor-fault rules on known injected events.
"""
from pathlib import Path
import shutil
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "outputs" / "exports" / "anomaly_detection_results.csv"
BACKUP = ROOT / "outputs" / "exports" / "anomaly_detection_results.before_showcase.csv"


def build_demo():
    rng = np.random.default_rng(27)
    n = 240
    times = pd.date_range("2026-10-20", periods=n, freq="h", tz="UTC")
    temp = 22 + 3*np.sin(np.arange(n)*2*np.pi/24) + rng.normal(0, .45, n)
    humidity = 58 + 5*np.sin(np.arange(n)*2*np.pi/30) + rng.normal(0, 1.2, n)
    pressure = 1013 + 2*np.sin(np.arange(n)*2*np.pi/72) + rng.normal(0, .35, n)
    truth = np.array(["NORMAL"]*n, dtype=object)
    # Known injected scenarios: spike, frozen sensor, and gradual drift.
    temp[80] = 49.0; truth[80] = "INJECTED_SPIKE"
    humidity[130:140] = humidity[129]; truth[130:140] = "INJECTED_FROZEN_STUCK"
    temp[185:205] += np.linspace(0, 9, 20); truth[185:205] = "INJECTED_DRIFT"
    df = pd.DataFrame({"timestamp": times.astype(str), "station_id": "DEMO-STATION-01",
                       "temperature": temp.round(2), "humidity": humidity.round(2), "pressure": pressure.round(2),
                       "Scenario_Type": truth})
    # Actual unsupervised detector, fitted only to this clearly-labelled demo batch.
    X = df[["temperature", "humidity", "pressure"]].to_numpy()
    model = IsolationForest(n_estimators=250, contamination=0.08, random_state=27)
    model.fit(X)
    raw = -model.score_samples(X)
    lo, hi = float(raw.min()), float(raw.max())
    score = (raw-lo)/(hi-lo) if hi > lo else np.zeros(n)
    model_flag = (model.predict(X) == -1).astype(int)
    # Explicit, interpretable rules for injected fault signatures.
    spike = (np.abs(df.temperature - df.temperature.rolling(7, min_periods=3).median()) > 10).fillna(False)
    frozen = df.humidity.rolling(5, min_periods=5).apply(lambda x: float(np.ptp(x) < 1e-9), raw=True).fillna(0).astype(bool)
    # Detect only unusually long repeated-value runs; expose as rule evidence.
    drift = (df.temperature - df.temperature.shift(10)).abs().gt(7.5).fillna(False)
    rule = (spike | frozen | drift).astype(int).to_numpy()
    df["IF_Anomaly"] = model_flag
    df["IF_Score"] = score.round(4)
    df["Ensemble_Anomaly"] = model_flag
    df["Ensemble_Score"] = score.round(4)
    df["Model_Agreement"] = model_flag  # one model is available in fallback demo; do not pretend four voted
    df["Models_Available"] = 1
    df["Rule_Anomaly"] = rule
    df["qc_failed"] = 0
    df["qc_flags"] = "[]"
    df["advisory_signal"] = ((score > .65) & (model_flag == 0)).astype(int)
    df["advisory_flags"] = np.where(df.advisory_signal.eq(1), "IsolationForest score elevated; review context", "")
    df["Final_Anomaly"] = ((model_flag == 1) | (rule == 1)).astype(int)
    df["Final_Score"] = np.maximum(score, rule).round(4)
    df["Anomaly_Severity"] = np.where(df.Final_Anomaly.eq(1), np.where(df.Final_Score > .8, "High", "Review"), "Normal")
    df["severity"] = df["Anomaly_Severity"].str.upper()
    df["root_cause"] = np.select([spike, frozen, drift], ["POSSIBLE_SPIKE", "POSSIBLE_FROZEN_SENSOR", "POSSIBLE_DRIFT"], default="UNKNOWN")
    df["event_type"] = df["root_cause"]
    df["explanation"] = np.select([spike, frozen, drift], ["Temperature sharply exceeds its local rolling baseline.", "Humidity is unchanged across a five-observation window.", "Temperature shows a sustained directional change."], default=np.where(model_flag == 1, "IsolationForest identified this multivariate observation as unusual relative to the demo batch.", "No detector or demonstration rule flagged this observation."))
    df["SHAP_Available"] = False
    df["SHAP_Top_Feature"] = "Unavailable"
    df["SHAP_Note"] = "Demo fallback uses IsolationForest; SHAP attribution is not computed."
    df["source_type"] = "SYNTHETIC_SHOWCASE"
    return df

if __name__ == "__main__":
    result = build_demo()
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    if EXPORT.exists() and not BACKUP.exists():
        shutil.copy2(EXPORT, BACKUP)
    result.to_csv(EXPORT, index=False)
    print("SkyGuard AI ANOMALY SHOWCASE ready")
    print(f"Rows: {len(result)} | Model: scikit-learn IsolationForest | Models available: 1")
    print("Injected cases: spike at row 81; frozen humidity rows 131-140; drift rows 186-205")
    print(f"Model-flagged rows: {int(result.IF_Anomaly.sum())}")
    print(f"Final flagged rows: {int(result.Final_Anomaly.sum())}")
    print("IMPORTANT: Synthetic demonstration only; not live data or validated accuracy.")
