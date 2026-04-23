# Personal Productivity, Health & Learning Analytics System

A complete data analytics system to track, analyse, and improve your daily habits across learning, health, and productivity — with an interactive Streamlit dashboard, ML-powered predictions, and a clean CLI for daily logging.

---

## Project structure

```
productivity_system/
├── core.py                  # Data models, scoring engine, recommendations, alerts
├── cli.py                   # Interactive daily log (run this every day)
├── dashboard.py             # Streamlit analytics dashboard
├── ml_model.py              # Random Forest + Gradient Boosting predictions
├── generate_sample_data.py  # Generate 90 days of demo data
├── requirements.txt
└── data/
    └── habit_log.csv        # Your persistent data store
```

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate demo data (optional — to explore the dashboard immediately)

```bash
python generate_sample_data.py
```

### 3. Launch the dashboard

```bash
streamlit run dashboard.py
```

Open http://localhost:8501 in your browser.

### 4. Log today's habits (run daily)

```bash
python cli.py
```

---

## Daily workflow

1. Each evening, run `python cli.py`
2. Answer the ~15 prompts (takes about 90 seconds)
3. See your scores, streaks, alerts, and recommendations instantly
4. Check the dashboard for deeper trend analysis

---

## Scoring system

| Score | Components |
|-------|-----------|
| **Learning score** | DSA tutorials (25pts) + GATE tutorials (20pts) + homework (15pts) + verbal (15pts) + revision (25pts) |
| **Health score** | Steps (25pts) + sleep hours (25pts) + sleep quality (15pts) + floors (10pts) + clean eating/supplements/oats/calorie deficit (25pts) |
| **Productivity score** | Coding tasks (40%) + learning score (40%) + health score (20%) |
| **Consistency index** | 7-day rolling average minus standard deviation |

All scores are on a 0–100 scale.

---

## Daily targets

| Metric | Target |
|--------|--------|
| DSA tutorials | 2/day |
| GATE tutorials | 2/day |
| GATE homework | 1/day |
| Verbal practice | 30 min |
| Revision | 60 min |
| Coding tasks | 3/day |
| Steps | 12,000 |
| Floors climbed | 10 |
| Sleep | 7.5 hours |

---

## ML predictions

The ML module trains a **Random Forest** and **Gradient Boosting** model (scikit-learn) to predict tomorrow's productivity score based on:

- Today's sleep, steps, and activity data
- Previous day's productivity (lag-1 feature)
- 7-day rolling average

Navigate to **ML Predictions** in the dashboard → click **Train / retrain model**.

You need at least 14 days of data before training is meaningful. 30+ days gives reliable predictions.

---

## Dashboard views

| View | What you see |
|------|-------------|
| **Dashboard** | KPIs, score trends, habit radar, alerts, recommendations, heatmap |
| **Trends** | 7-day rolling averages, health metrics over time, learning metrics |
| **Correlations** | Correlation matrix, sleep vs productivity scatter, steps vs health |
| **ML Predictions** | Train model, see tomorrow's forecast, feature importance chart |
| **Raw Data** | Full table, CSV export, weekly summary |

---

## Customising targets

Edit the `TARGETS` dict in `core.py`:

```python
TARGETS = {
    "steps": 12_000,
    "floors_climbed": 10,
    "sleep_hours": 7.5,
    "verbal_practice_mins": 30,
    "revision_mins": 60,
    "coding_tasks": 3,
    "dsa_tutorials": 2,
    "gate_tutorials": 2,
    "gate_homework": 1,
}
```

---

## Adding new habit fields

1. Add the field name to `FIELDS` in `core.py`
2. Add it as an attribute on `DayEntry`
3. Wire it into `compute_scores()` with a weight
4. Add the input prompt in `cli.py`
5. Add it to `FEATURES` in `ml_model.py`

---

## Exporting reports

From the **Raw Data** view, click **Download CSV** to export the full dataset. You can then open it in Excel, Google Sheets, or Power BI for further analysis.

---

## Technologies

- **Python** — core logic, scoring, CLI
- **Pandas / NumPy** — data processing
- **Plotly** — interactive charts
- **Streamlit** — web dashboard
- **scikit-learn** — Random Forest & Gradient Boosting

---

## Roadmap / bonus features

- [ ] Google Sheets sync (via `gspread`)
- [ ] Automated daily reminder via cron + email
- [ ] PDF report export
- [ ] Mobile-friendly input via Telegram bot
- [ ] Notion integration
