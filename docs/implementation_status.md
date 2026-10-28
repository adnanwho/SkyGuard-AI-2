# SkyGuard AI — Implementation Status

This document merges and supersedes three previously separate, overlapping,
and partly contradictory status files (`IMPLEMENTATION_REPORT.md`,
`IMPLEMENTATION_STATUS.md`, `IMPLEMENTATION_ROADMAP.md`), consolidated during
the repository cleanup on 2026-09-16. Their full original text is preserved
in `archive/legacy/docs/` for traceability. Where the old files disagreed
(e.g. differing counts of "passing tests" across entries — 8, 12, 24, and
28), this document defers to the **most recent, most specific** figure and
says so explicitly rather than repeating stale numbers.

**Project status:** Local MVP implemented and runnable. Not a production
service.

## Implemented

### Data and processing
- Canonical weather observation schema
- Legacy and canonical CSV ingestion
- Deterministic multi-station simulation
- Controlled anomaly injection with ground-truth labels
- Timestamp ordering and preprocessing
- Missingness, gaps, duplicates, range, rate, persistence, and thermodynamic QC
- Leakage-safe temporal and derived feature engineering

### Detection and diagnosis
- Isolation Forest anomaly detection
- ECOD, COPOD, and HBOS ensemble detection
- Clean-baseline training and persisted scoring
- Temporal and spatial context
- Regional weather-event detection
- Isolated sensor-fault detection
- Root-cause classification for spikes, frozen sensors, drift, and communication/missing data
- Severity and confidence scoring

### Explainability and operations
- Row-level SHAP feature attribution when the optional dependency is installed
- Explicit SHAP-unavailable fallback state
- Plain-language anomaly explanations
- Sensor health scores and status
- Maintenance recommendations
- Recovery suggestions, with original observations kept immutable
- Row-by-row replay with measured processing latency
- Reproducible evaluation scenarios and metrics

### Engine
- `src.skyguard.engine.SkyGuardEngine` is the canonical programmatic
  processing boundary. It returns a `SkyGuardResult` with summary,
  observations, anomalies, sensor health, diagnostics, metrics, and timings.
- `main.py`, `server.py`, and the dashboard are all routed through this
  single engine — there is one pipeline, not several parallel ones.
- Explicit empty-input and invalid-schema boundary behavior is handled.

### Dashboards (two, serving different purposes — see `docs/architecture.md`)
- **Streamlit** (`dashboard/app.py`): Dashboard, Stations, Anomalies, Sensor
  Health, Evaluation, Replay, Data Source, and Settings pages; KPI cards;
  prioritized anomaly queue; trend charts; CSV upload handling.
- **Web console** (`web/`): vanilla JS/HTML/CSS frontend backed by the
  stdlib HTTP server in `server.py` (`GET /api/data`, `POST /api/refresh`),
  running the real pipeline on demand rather than reading a static export.

### Validation (most recent recorded run)
- `python -m pytest -q`: **28 passed** (four engine-contract tests were
  added after the earlier 24-test snapshot; see "Test count history" below).
- `python main.py --input data/processed/SkyGuard_clean_3hourly.csv`:
  successful; 9,360 observations processed, 155 anomalies detected.
- Streamlit startup smoke test: successful HTTP response.

**Test count history** (for traceability, not because it matters going
forward): 8 → 12 → 24 → 28 passed, recorded across successive development
sessions as layers were added. The repository audit (`docs/repository_audit.md`,
2026-09-16) independently counted **28 test functions** in the current
`tests/` tree by direct inspection, which matches the last recorded run.
None of these historical numbers were re-verified by executing the suite
during the 2026-09-16 cleanup — `pytest` was not installable in that
environment. Treat 28 as "implemented; last known to pass," not
"implemented and verified today."

## Not Implemented or Not Production-Ready

### Advanced modeling
- LSTM autoencoder training/scoring is implemented in
  `src/skyguard/context/temporal.py` but requires TensorFlow, which is an
  optional, commented-out dependency. `python main.py --lstm-status` reports
  availability honestly.
- Model quality, especially weather-event recall, needs improvement.

### Production infrastructure (explicitly out of MVP scope)
- Live MQTT, Kafka, or WIS2.0 ingestion
- Cloud deployment, production database
- REST API, authentication/authorization
- Production monitoring and alerting
- ESP32 or edge deployment

### Operational limitations
- This is a local batch prototype, not a production service.
- Dashboard replay does not yet provide full live-style pause/reset.
- The dashboard uses station comparison and spatial evidence rather than a
  coordinate map.
- Evaluation page provides summary metrics; no confusion-matrix
  visualization yet.

## Current Measured Evaluation

Two evaluation snapshots exist in the project history, from before and
after the engine-stabilization refactor. Neither has been re-run during
cleanup; both are reported as measured historical results, not guarantees:

| Metric | Pre-stabilization | Post-stabilization |
|---|---|---|
| Precision | 0.714 | 0.400 |
| Recall | 0.500 | 0.643 |
| F1 | 0.560 | 0.493 |
| False-positive rate | 0.061 | 0.205 |
| Weather-event recall | 0.333 | 0.500 |

The post-stabilization run trades precision for recall. This was an
observed side effect of the refactor, not a deliberate tuning target — it
is flagged here rather than silently dropped, per the "never fabricate
results" rule.

## Roadmap (unimplemented work, ordered by priority)

### Priority 0: Core MVP completion
1. Structured, machine-readable QC results per rule category, preserving
   multiple violations per observation.
2. Canonical pipeline contract with fully structured observation / quality
   / anomaly / context / diagnosis / explanation / health / maintenance /
   recovery fields.
3. Full separation of baseline training from inference in the main
   pipeline (currently the model is refit on each batch).
4. Evaluation completeness: per-root-cause metrics, event-vs-fault metrics,
   confusion matrices, measured latency.
5. Dashboard: surface QC evidence, spatial evidence, recovery state, and
   baseline/model status directly in the operator workflow.

### Priority 1: Intelligence quality
1. Station metadata and real coordinate-based neighbor selection.
2. Configurable-window temporal persistence, drift, and trend evidence.
3. Rolling (not cumulative) health, trend, and recovery behavior.
4. Additional evaluation scenarios: seasonal-extreme, repeated-fault.

### Priority 2: Advanced modules
1. LSTM autoencoder, only once TensorFlow is an explicit installed
   dependency — not a placeholder.
2. Sequence reconstruction error as a separate temporal evidence signal.
3. Model-based recovery, after raw-value immutability and evaluation are
   fully established.

### Priority 3: Classical AI syllabus modules

Tracked separately in `docs/syllabus_mapping.md`. Not part of the
application roadmap above — these are the academic search / adversarial
search / knowledge representation / uncertainty-reasoning modules required
for the B.Tech syllabus, layered on top of (not replacing) the application
described in this document.

### Priority 4: Production scope (explicitly out of MVP)
- MQTT/Kafka/WIS2 ingestion, cloud deployment, production database
- Authentication/authorization, REST API
- ESP32/edge deployment, predictive failure-date modeling

## Definition of Done

A roadmap item is complete only when its code, a focused test, a documented
interface, and executable validation evidence all exist. Advanced and
production capabilities remain visibly unavailable (reported as such by the
relevant `--status` flag or dashboard state) until every condition is met.
