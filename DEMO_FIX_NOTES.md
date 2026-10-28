# SkyGuard AI demo fixes — 2026-10-25

## Why the dashboard showed 0/4 models, 100%, CRITICAL

The saved export confirms that these are separate signals. In the inspected data, 6,190 rows have `Rule_Anomaly=1` and `qc_failed=True`; those rows receive `Final_Score=1.0` and `severity=CRITICAL` even when `Model_Agreement=0` and `Ensemble_Anomaly=0`. The final prediction combines ensemble and rule alerts, so a rule/QC-only alert can legitimately exist without model consensus. The prior UI obscured that distinction by displaying `Final_Score` as a model score and the generic severity as the status.

## Changes

- Table now labels the score column **Model score** and uses `Ensemble_Score` rather than the fused `Final_Score`.
- Rule/QC alerts show **QC ALERT** or **RULE ALERT** instead of implying that the model ensemble agreed.
- The detail dialog separately reports model agreement, model score, and rule/QC evidence.
- Detector values that are absent or nonnumeric are shown as **UNAVAILABLE**, not as normal votes.
- Model denominator is based on available detector outputs, rather than always assuming four are available.
- The API now includes `Rule_Anomaly`, which the frontend needs to distinguish rule-based detections.

## Validation performed

- `node --check web/app.js` — passed.
- `python -m py_compile server.py` — passed.
- Local server smoke test — `/api/health` responded successfully and `/api/data` returned 9,360 rows with `Rule_Anomaly` included.

## Limitations

This patch corrects UI interpretation; it does not claim that the underlying rule thresholds or anomaly labels are scientifically validated. `Final_Score` remains a fused score where rule alerts can force it to 1.0; it should not be interpreted as a calibrated probability. Full model re-analysis still depends on the repository's Python dependencies.
