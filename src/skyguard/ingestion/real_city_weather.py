"""Real-city weather ingestion and historical-trained four-model anomaly detection.

Open-Meteo historical values are gridded reanalysis/model estimates, not direct
station observations. Current values are forecast-model products. Provenance is
returned with every result so the UI must not describe these as physical sensors.
"""
from __future__ import annotations
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
import requests
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

CITIES = {
    "Delhi": {"latitude": 28.6139, "longitude": 77.2090},
    "Mumbai": {"latitude": 19.0760, "longitude": 72.8777},
    "Bengaluru": {"latitude": 12.9716, "longitude": 77.5946},
    "Chennai": {"latitude": 13.0827, "longitude": 80.2707},
    "Kolkata": {"latitude": 22.5726, "longitude": 88.3639},
}
VARS = ["temperature_2m", "relative_humidity_2m", "surface_pressure"]
FEATURES = ["temperature_2m", "relative_humidity_2m", "surface_pressure",
            "temperature_delta", "humidity_delta", "pressure_delta",
            "temperature_deviation", "humidity_deviation", "pressure_deviation"]
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "SkyGuardAI/1.0 (educational anomaly monitoring)"})


def _get_json(url, params, timeout=25):
    response = SESSION.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _hourly_frame(payload, city):
    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        raise ValueError(f"No hourly weather values returned for {city}")
    df = pd.DataFrame({
        "timestamp": pd.to_datetime(times, errors="coerce"),
        "temperature_2m": hourly.get("temperature_2m", []),
        "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
        "surface_pressure": hourly.get("surface_pressure", []),
    })
    df["city"] = city
    df["latitude"] = CITIES[city]["latitude"]
    df["longitude"] = CITIES[city]["longitude"]
    for c in VARS:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df.dropna(subset=VARS).sort_values("timestamp").reset_index(drop=True)


def fetch_city_history(city, days=60):
    """Fetch hourly archive data for model fitting; default is last 60 complete days."""
    if city not in CITIES:
        raise ValueError(f"Unsupported city: {city}")
    end = (datetime.now(timezone.utc).date() - timedelta(days=2))
    start = end - timedelta(days=max(14, min(int(days), 365)))
    p = {**CITIES[city], "start_date": start.isoformat(), "end_date": end.isoformat(),
         "hourly": ",".join(VARS), "timezone": "UTC"}
    payload = _get_json("https://archive-api.open-meteo.com/v1/archive", p)
    df = _hourly_frame(payload, city)
    df["data_source"] = "Open-Meteo Historical Weather API (reanalysis/model estimate)"
    df["data_role"] = "training_history"
    return df


def fetch_city_current(city):
    """Fetch current conditions plus the most recent hourly point from forecast model API."""
    if city not in CITIES:
        raise ValueError(f"Unsupported city: {city}")
    p = {**CITIES[city], "current": ",".join(VARS), "hourly": ",".join(VARS),
         "past_hours": 24, "forecast_hours": 1, "timezone": "UTC"}
    payload = _get_json("https://api.open-meteo.com/v1/forecast", p)
    df = _hourly_frame(payload, city)
    # Score the most recent available hourly points, not future forecast rows.
    now = pd.Timestamp.now(tz="UTC").tz_localize(None)
    df = df[df["timestamp"] <= now].tail(24).copy()
    if df.empty:
        current = payload.get("current", {})
        stamp = pd.to_datetime(current.get("time"), errors="coerce")
        if pd.isna(stamp):
            raise ValueError(f"No current or past-hour data returned for {city}")
        df = pd.DataFrame([{"timestamp": stamp, **{v: current.get(v) for v in VARS},
                            "city": city, "latitude": CITIES[city]["latitude"],
                            "longitude": CITIES[city]["longitude"]}])
    df["data_source"] = "Open-Meteo Forecast API (weather-model estimate, refreshed on request)"
    df["data_role"] = "current_context"
    return df.reset_index(drop=True)


def _features(history, scored):
    """Build causal features; rolling baselines use preceding observations only."""
    both = pd.concat([history.assign(_role="history"), scored.assign(_role="score")], ignore_index=True)
    both = both.sort_values("timestamp").reset_index(drop=True)
    for source, prefix in [("temperature_2m", "temperature"),
                           ("relative_humidity_2m", "humidity"),
                           ("surface_pressure", "pressure")]:
        both[f"{prefix}_delta"] = both[source].diff()
        previous = both[source].shift(1)
        rolling_mean = previous.rolling(24, min_periods=6).mean()
        both[f"{prefix}_deviation"] = both[source] - rolling_mean
    # Training rows with incomplete warm-up features are excluded, never backfilled.
    train = both[both["_role"] == "history"].dropna(subset=FEATURES).copy()
    score = both[both["_role"] == "score"].dropna(subset=FEATURES).copy()
    return train, score


def detect_city(city, days=60):
    """Train IsolationForest + ECOD + COPOD + HBOS on history, score current context."""
    started = time.time()
    history = fetch_city_history(city, days=days)
    current = fetch_city_current(city)
    train, score = _features(history, current)
    if len(train) < 200:
        raise ValueError(f"Not enough valid historical feature rows for {city}: {len(train)}")
    if score.empty:
        raise ValueError(f"No current rows have enough preceding context for {city}")
    # Keep all four previously used detectors. Do not silently downgrade to one model.
    try:
        from pyod.models.ecod import ECOD
        from pyod.models.copod import COPOD
        from pyod.models.hbos import HBOS
    except ImportError as exc:
        raise RuntimeError("Missing dependency 'pyod'. Install project requirements to run the four-model ensemble; no fallback model was used.") from exc
    scaler = StandardScaler()
    X_train = scaler.fit_transform(train[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0.0))
    X_score = scaler.transform(score[FEATURES].replace([np.inf, -np.inf], np.nan).fillna(0.0))
    models = {
        "Isolation Forest": IsolationForest(n_estimators=300, contamination=0.02, random_state=42, n_jobs=-1),
        "ECOD": ECOD(contamination=0.02),
        "COPOD": COPOD(contamination=0.02),
        "HBOS": HBOS(contamination=0.02),
    }
    rows = []
    for name, model in models.items():
        model.fit(X_train)
        if name == "Isolation Forest":
            decision = -model.decision_function(X_score)
            threshold = float(np.quantile(-model.decision_function(X_train), 0.98))
            flagged = decision >= threshold
        else:
            decision = np.asarray(model.decision_function(X_score), dtype=float)
            threshold = float(np.quantile(np.asarray(model.decision_scores_, dtype=float), 0.98))
            flagged = decision >= threshold
        # Historical-only thresholds prevent fitting on the current observations.
        train_scores = (-model.decision_function(X_train) if name == "Isolation Forest"
                        else np.asarray(model.decision_scores_, dtype=float))
        threshold = float(np.quantile(train_scores, 0.98))
        flagged = decision >= threshold
        for i, (_, row) in enumerate(score.iterrows()):
            rows.append({"timestamp": row["timestamp"].isoformat(), "city": city,
                         "latitude": row["latitude"], "longitude": row["longitude"],
                         "temperature_c": float(row["temperature_2m"]),
                         "humidity_pct": float(row["relative_humidity_2m"]),
                         "pressure_hpa": float(row["surface_pressure"]),
                         "model": name, "model_score": float(decision[i]),
                         "threshold": threshold, "is_anomaly": bool(flagged[i]),
                         "data_source": row["data_source"],
                         "training_rows": int(len(train)), "history_days_requested": int(days)})
    result = pd.DataFrame(rows)
    pivot = result.pivot(index=["timestamp", "city", "latitude", "longitude", "temperature_c", "humidity_pct", "pressure_hpa", "data_source", "training_rows", "history_days_requested"], columns="model", values="is_anomaly").reset_index()
    model_cols = list(models.keys())
    pivot["models_available"] = len(model_cols)
    pivot["models_agreed"] = pivot[model_cols].astype(bool).sum(axis=1)
    pivot["ensemble_anomaly"] = pivot["models_agreed"] >= 3
    pivot["ensemble_agreement_pct"] = (pivot["models_agreed"] / len(model_cols) * 100).round(1)
    pivot["data_provenance"] = "Historical model-trained baseline; current weather-model context; not direct station telemetry"
    result_records = pivot.sort_values("timestamp").to_dict(orient="records")
    for r in result_records:
        r["timestamp"] = str(r["timestamp"])
        for k, v in list(r.items()):
            if isinstance(v, (np.bool_,)): r[k] = bool(v)
            elif isinstance(v, (np.integer,)): r[k] = int(v)
            elif isinstance(v, (np.floating,)): r[k] = float(v)
    return {"city": city, "coordinates": CITIES[city], "historical_rows": int(len(history)),
            "training_feature_rows": int(len(train)), "current_rows_scored": int(len(score)),
            "models": list(models.keys()), "source": "Open-Meteo historical archive + forecast API",
            "provenance": "Gridded/reanalysis and forecast-model estimates; not direct local sensor observations.",
            "fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "elapsed_seconds": round(time.time() - started, 2), "results": result_records}


def list_cities():
    return [{"city": name, **coords} for name, coords in CITIES.items()]
