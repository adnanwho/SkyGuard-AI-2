"""Compare local observations with Open-Meteo historical reanalysis context.

This is an optional corroboration tool, not ground truth. Open-Meteo grid-cell
values can differ from local station observations. Raw input is never modified.

Usage:
  python scripts/compare_open_meteo.py \
    --input data/processed/SkyGuard_clean_3hourly.csv \
    --output outputs/exports/open_meteo_comparison.csv
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import pandas as pd
import requests

# Approximate city-center coordinates only. Replace with real station coordinates
# when available; these are not claimed to be the coordinates of source sensors.
CITY_COORDINATES = {
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Kolkata": (22.5726, 88.3639),
    "Mumbai": (19.0760, 72.8777),
    "New_Delhi": (28.6139, 77.2090),
}
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


def fetch_city(session: requests.Session, city: str, latitude: float, longitude: float,
               start_date: str, end_date: str) -> pd.DataFrame:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": "temperature_2m,relative_humidity_2m,pressure_msl",
        "timezone": "Asia/Kolkata",
    }
    response = session.get(ARCHIVE_URL, params=params, timeout=45)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(f"Open-Meteo error for {city}: {payload.get('reason', 'unknown error')}")
    hourly = payload.get("hourly") or {}
    times = hourly.get("time", [])
    if not times:
        raise RuntimeError(f"Open-Meteo returned no hourly records for {city}")
    return pd.DataFrame({
        "timestamp": pd.to_datetime(times),
        "station_id": city,
        "external_temperature": hourly.get("temperature_2m", []),
        "external_humidity": hourly.get("relative_humidity_2m", []),
        "external_pressure": hourly.get("pressure_msl", []),
        "external_source": "Open-Meteo Historical Weather API (reanalysis)",
        "external_latitude": payload.get("latitude", latitude),
        "external_longitude": payload.get("longitude", longitude),
    })


def compare(input_path: Path, output_path: Path, sleep_seconds: float = 0.5) -> pd.DataFrame:
    source = pd.read_csv(input_path)
    aliases = {"Location": "station_id", "DateTime": "timestamp", "Temperature_C": "temperature",
               "Humidity_Percent": "humidity", "Pressure_hPa": "pressure"}
    source = source.rename(columns=aliases)
    required = {"station_id", "timestamp", "temperature", "humidity", "pressure"}
    missing = required - set(source.columns)
    if missing:
        raise ValueError(f"Input missing required columns: {sorted(missing)}")
    source["timestamp"] = pd.to_datetime(source["timestamp"], errors="raise")
    source["station_id"] = source["station_id"].astype(str)
    start_date = source["timestamp"].min().date().isoformat()
    end_date = source["timestamp"].max().date().isoformat()
    session = requests.Session()
    external = []
    for index, city in enumerate(sorted(source["station_id"].unique())):
        if city not in CITY_COORDINATES:
            print(f"SKIP {city}: no explicit coordinate mapping; provide real coordinates rather than guessing.")
            continue
        lat, lon = CITY_COORDINATES[city]
        print(f"Fetching Open-Meteo context for {city}: {start_date} to {end_date}")
        external.append(fetch_city(session, city, lat, lon, start_date, end_date))
        if index < len(source["station_id"].unique()) - 1:
            time.sleep(max(0, sleep_seconds))
    if not external:
        raise ValueError("No stations could be mapped to external context")
    ext = pd.concat(external, ignore_index=True)
    # Use nearest hourly model grid-cell value within 90 minutes of the local
    # timestamp; preserve all original values and report the differences.
    merged = pd.merge_asof(
        source.sort_values("timestamp"), ext.sort_values("timestamp"),
        on="timestamp", by="station_id", direction="nearest", tolerance=pd.Timedelta("90min"),
        suffixes=("", "_external"),
    )
    merged["temperature_delta_vs_external"] = merged["temperature"] - merged["external_temperature"]
    merged["humidity_delta_vs_external"] = merged["humidity"] - merged["external_humidity"]
    merged["pressure_delta_vs_external"] = merged["pressure"] - merged["external_pressure"]
    merged["external_match_available"] = merged["external_temperature"].notna()
    merged["external_context_note"] = (
        "Context only: gridded reanalysis is not station ground truth; investigate differences, do not auto-relabel."
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    print(f"Wrote {len(merged)} comparison rows to {output_path}")
    print(f"External matches: {int(merged['external_match_available'].sum())}/{len(merged)}")
    return merged


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/processed/SkyGuard_clean_3hourly.csv"))
    parser.add_argument("--output", type=Path, default=Path("outputs/exports/open_meteo_comparison.csv"))
    parser.add_argument("--sleep-seconds", type=float, default=0.5)
    args = parser.parse_args()
    compare(args.input, args.output, args.sleep_seconds)


if __name__ == "__main__":
    main()
