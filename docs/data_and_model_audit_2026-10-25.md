# SkyGuard AI data and model audit — 2026-10-25

## Scope

Audited the supplied project ZIP, the active Python QC/pipeline/detector code, `data/processed/SkyGuard_clean_3hourly.csv`, `data/processed/SkyGuard_features.csv`, `outputs/exports/anomaly_detection_results.csv`, `outputs/exports/simulated_results.csv`, and `outputs/evaluation/latest.csv`.

## Confirmed findings

1. The processed input has 9,360 rows, five station labels, 1,883 distinct timestamps, no nulls in the three sensor columns, and a period from 2025-01-01 through 2025-08-24. Its provenance is not recorded in the active data README or as row-level metadata, so it cannot be certified as observed station data from this repository alone.
2. In the saved 9,360-row export, `qc_failed=True` and `Rule_Anomaly=1` both occur 6,190 times. `humidity_deviation_fail` occurs 5,710 times; humidity and temperature drift flags are also common. This is a strong indication that rolling statistical deviations are being treated too aggressively as hard failures for these data.
3. The old QC implementation defined `qc_failed` as any `*_fail` column. That included statistical baseline deviation and drift. The pipeline also OR-ed those same soft signals into `Rule_Anomaly`, so normal weather transitions could dominate the final result.
4. The four unsupervised models are fit on the same batch being scored in `run_anomaly_pipeline`. Their scores are min-max normalized over that batch. Those scores are relative within a run and are not calibrated probabilities; fitting and scoring on the same batch is not a production-style held-out evaluation.
5. The saved evaluation export contains 160 rows: 132 `NORMAL`, 12 `WEATHER_EVENT`, and only four rows for each of `SPIKE`, `FROZEN_STUCK`, `DRIFT_BIAS`, and `COMMUNICATION_MISSING`. This is useful for a smoke test, not sufficient evidence of broad performance or external generalization.
6. `data/raw/README.md` is a placeholder and no active collector is configured. Historical external data comparison was not previously integrated.
7. The current runtime cannot import `pyod`, so the full ensemble pipeline and package-level pytest collection are blocked until project dependencies are installed. No post-change model-performance result is claimed here.

## Changes in this patch

- Split hard QC failures from statistical advisory signals. Physical range, rate, missingness, timestamp gaps, duplicates, persistence, and thermodynamic inconsistency remain hard QC failures. Short-window deviation and drift remain visible as advisory evidence and are no longer automatically promoted to hard QC failure.
- Added `advisory_signal` and `advisory_flags` fields.
- Changed final rule-alert fusion to use hard QC only, alongside the ensemble's own decision. Statistical advisories remain visible for investigation.
- Added a CSV comparison utility for Open-Meteo Historical Weather API reanalysis. It adds contextual temperature, relative humidity, and mean sea-level pressure comparisons without overwriting original observations or relabeling ground truth.
- Added tests for the distinction between advisory deviation and hard physical-range failure.

## External data source caveats

The Open-Meteo archive provides gridded reanalysis, not the exact readings from the user's sensor. The utility uses approximate city-center coordinates because the source CSV has no station coordinates. Differences can reflect grid-cell location, elevation, observation timing, and station-vs-reanalysis characteristics. External comparisons must be treated as corroborating context, not ground truth, and must not be used to automatically rewrite labels.

API documentation: https://open-meteo.com/en/docs/historical-weather-api

## Required next steps

1. Install dependencies from `requirements.txt` in a project virtual environment, then run the complete test suite and regenerate the results export.
2. Run the Open-Meteo comparison utility for the historical date window and inspect matched-row coverage and differences.
3. Add real station coordinates and source/license/provenance metadata before interpreting external comparison as station validation.
4. Establish a chronological holdout, tune thresholds only on validation data, and report per-class metrics with support.
5. Consider a trained novelty-detection workflow where models are fit on a clean training partition and score unseen data. Do not add more unsupervised models merely to increase the vote count.
