# Run a real anomaly-detection showcase (no PyOD required)

Your project should visibly demonstrate anomaly detection, not only saved historic results. This script creates a clearly labelled synthetic sensor series, injects a temperature spike, a frozen humidity sensor, and a temperature drift, then runs scikit-learn IsolationForest plus transparent diagnostic rules.

## Run it

From the project root:

```bash
python scripts/run_anomaly_showcase.py
python server.py
```

Then open the local URL printed by the server and refresh the dashboard. The script writes `outputs/exports/anomaly_detection_results.csv`. It preserves the pre-showcase export as `outputs/exports/anomaly_detection_results.before_showcase.csv` the first time it runs. Restore that backup after your presentation if you want the original saved dataset back.

## What to say in the showcase

“This is a reproducible synthetic demonstration. We injected known sensor faults and run an actual IsolationForest detector plus explicit diagnostic rules. The known injection labels let us inspect whether the system reacts to the expected patterns. This is not a real-world accuracy claim.”

The fallback intentionally reports one available ML model, not four. The original ECOD/COPOD/HBOS ensemble requires `pyod`; this demo does not pretend those models ran. The IsolationForest score is a relative anomaly score, not a calibrated probability.
