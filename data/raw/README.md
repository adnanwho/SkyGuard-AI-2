# Raw Data

Place original downloaded or uploaded weather-station files here. Raw files are not modified by the pipeline. Processed and evaluation datasets belong in their respective directories.

# Option A: Live server with API + dashboard

python server.py

# Then open <http://127.0.0.1:8137/>

# Option B: Streamlit dashboard (separate from browser frontend)

streamlit run dashboard/app.py

# Option C: CLI pipeline

python main.py
python main.py --simulate
python main.py --evaluate
