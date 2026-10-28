# SkyGuard AI — 1-hour showcase quick start

## Why does a row say ADVISORY / REVIEW?

`ADVISORY` means a statistical baseline-deviation or possible-drift rule fired. It is an investigation hint, not a confirmed anomaly. A row is a confirmed alert only when `Final_Anomaly=1` (ensemble detection or hard QC). The dashboard now makes these categories visually distinct and includes a dedicated **Advisory review** filter.

## Recommended demo sequence

1. Run `run_demo.bat` from this project folder and keep the server terminal open.
2. Open the local dashboard URL printed by the launcher.
3. Show the overview counts and the detection log.
4. Select **Confirmed alerts** to show final alerts; open a row to inspect its detector/QC evidence.
5. Select **Advisory review** to show non-blocking deviation/drift signals. Explain that these require context and are not model-confirmed anomalies.
6. Select **No alert / advisory** to show rows with neither a final alert nor an advisory signal.
7. Click refresh only if dependencies are installed and the pipeline is available; otherwise present the saved analysis as historical/precomputed results.

## Honest limitations to mention

- The stored CSV covers 9,360 observations. In this saved export, 237 rows have `Final_Anomaly=1`, 5,957 rows are advisory-only, and 3,166 rows have neither a final alert nor advisory. These counts describe the saved export, not live telemetry.
- Detector scores are not calibrated probabilities.
- External weather comparison is contextual only and does not establish sensor ground truth.
- If `pyod` is unavailable, the full ensemble cannot be rerun in that environment; do not describe saved results as a fresh run.

## Quick validation

From the repository root:

```bash
node --check web/app.js
python -m compileall -q src server.py
```

Run the full project test suite after installing the dependencies from `requirements.txt`.
