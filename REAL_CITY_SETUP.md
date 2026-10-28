# Real-city weather anomaly screening

This mode adds five real Indian city locations: Delhi, Mumbai, Bengaluru, Chennai and Kolkata.

## Data and model design

- Historical training data: Open-Meteo Historical Weather API (`archive-api.open-meteo.com`), hourly temperature at 2m, relative humidity at 2m, and surface pressure.
- Current context: Open-Meteo Forecast API (`api.open-meteo.com`), latest available past-hour values returned alongside current conditions.
- Model detectors: the same four detector families used in the existing SkyGuard ensemble: Isolation Forest, ECOD, COPOD and HBOS.
- Models are fitted on historical rows only and score recent current-context rows. The model is retrained per requested city/run; this version does not persist fitted models.
- The consensus rule is 3 of 4 detectors. A flagged row is a candidate anomaly relative to the training distribution, not proof of a sensor failure.

**Important provenance caveat:** Open-Meteo archive data is gridded historical reanalysis/model output, and its forecast API is numerical weather model output. Neither is direct telemetry from a physical station. The product labels this honestly. To validate actual station faults, integrate a ground-truth station feed (for example, authorized IMD/other station data) and compare observations against it.

## Install and run (Windows)

```powershell
python -m pip install -r requirements.txt
python server.py
```

Open `http://127.0.0.1:8137/real-cities.html`.

The new endpoint `POST /api/real-cities/analyze` accepts JSON such as `{"city":"Delhi","days":60}`. `days` must be 14–365. First request downloads historical and current-context data and trains all four models; it can take tens of seconds and requires internet access.

`GET /api/real-cities` lists the configured city names and coordinates.

## Troubleshooting

- If `pyod` is missing, install the full `requirements.txt`. The API returns a clear error; it does not claim that four models ran if they did not.
- If Open-Meteo is unreachable, check internet/firewall and retry.
- Public API availability/rate limits can change; cache fetched history before repeated demos if needed.
- This is a research/demo workflow, not an operational alerting service. It does not currently persist trained models or use ground-truth labels for supervised evaluation.
