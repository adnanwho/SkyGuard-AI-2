# SkyGuard AI

SkyGuard AI is a local Python MVP for quality control and anomaly detection in Automatic Weather Station observations. It combines deterministic QC, feature-based ensemble detection, temporal/spatial context, fault diagnosis, sensor health, maintenance recommendations, and evaluation.

## Current status

Implemented:

- Canonical and legacy CSV ingestion
- Deterministic multi-station simulation and labeled anomaly injection
- Range, rate, missingness, duplicate, persistence, and thermodynamic QC
- Leakage-safe temporal feature engineering
- Isolation Forest, ECOD, COPOD, and HBOS ensemble detection
- Spatial/temporal context and event-versus-fault diagnosis
- Severity, confidence, explanations, health, maintenance, and recovery suggestions
- Batch pipeline, evaluation metrics, CLI, Streamlit dashboard, and tests

Future work:

- LSTM autoencoder training and scoring when TensorFlow is installed
- Live ingestion and production deployment

SHAP feature attribution is active when installed and is included in the pipeline output. It reports feature contribution, not causal proof.

Additional commands:

```bash
python main.py --train-baseline
python main.py --score-baseline
python main.py --evaluate
python main.py --lstm-status
python main.py --train-lstm
```

## Project structure

Runtime code lives under `src/skyguard` and is organized by ingestion, preprocessing, features, detection, context, diagnosis, explainability, health, evaluation, and replay. The Streamlit entry point is `dashboard/app.py`. Generated model and export artifacts live under `models/trained`, `outputs/exports`, and `outputs/evaluation`.

## Setup

```bash
python -m pip install -r requirements.txt
```

## Run

```bash
python main.py --input data/processed/SkyGuard_clean_3hourly.csv
```

The command writes `outputs/exports/anomaly_detection_results.csv`. To run a deterministic demo dataset:

```bash
python main.py --simulate --output outputs/exports/simulated_results.csv
```

To launch the dashboard:

```bash
streamlit run dashboard/app.py
```

## Test

```bash
python -m pytest -q
```

For development guidance, see [docs/development.md](docs/development.md) and [docs/architecture.md](docs/architecture.md).

## Quick prototype demo (Windows)

1. Extract the repository ZIP into a normal folder.
2. Double-click `run_demo.bat`. If Windows asks for permission, allow Python to run locally.
3. Open `http://127.0.0.1:8137/` in your browser. Keep the terminal window open while presenting.
4. The dashboard loads the latest saved analysis from `outputs/exports/anomaly_detection_results.csv`. Click an observation to inspect its saved detector and QC evidence.

The dashboard and saved results can work even if the ML dependencies are not installed. Re-running the full detector pipeline requires the dependencies in `requirements.txt`; the server exposes `http://127.0.0.1:8137/api/health` to show whether the pipeline dependencies are available. If refresh fails, the dashboard keeps the saved results available instead of leaving the page blank.

To install dependencies before rerunning analysis, open a terminal in the project folder and run `python -m pip install -r requirements.txt`. Then restart the server and use the refresh button. Installation may take several minutes and is not required merely to present the saved-results prototype.

## Data audit and optional external weather context

The provenance of `data/processed/SkyGuard_clean_3hourly.csv` is not recorded in the current repository. Treat it as an unverified historical dataset until its source is documented. The saved evaluation dataset is synthetic and should not be presented as real-world validation.

The QC pipeline now separates hard data-quality failures from rolling baseline deviation/drift advisories. Advisories are shown for investigation but do not automatically become final anomalies. This avoids treating ordinary weather changes as confirmed sensor failures; thresholds still require calibration against documented station data.

To compare the processed city observations with Open-Meteo historical reanalysis (requires internet access):

```bash
python scripts/compare_open_meteo.py \
  --input data/processed/SkyGuard_clean_3hourly.csv \
  --output outputs/exports/open_meteo_comparison.csv
```

The tool uses approximate city-center coordinates because the source CSV does not include station coordinates. It preserves original values and adds comparison columns. Reanalysis is gridded context, not station ground truth; do not automatically relabel observations from this comparison. See `docs/data_and_model_audit_2026-10-25.md`.
