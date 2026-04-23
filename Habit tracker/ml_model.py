"""
Machine Learning prediction module.
Trains a Random Forest and Gradient Boosting model on historical habit data
to predict next-day productivity score.
"""

import json
import pickle
from pathlib import Path

import numpy as np

MODELS_DIR = Path(__file__).parent / "models"
MODELS_DIR.mkdir(exist_ok=True)
RF_PATH  = MODELS_DIR / "random_forest.pkl"
GB_PATH  = MODELS_DIR / "gradient_boost.pkl"
META_PATH= MODELS_DIR / "model_meta.json"

FEATURES = [
    "sleep_hours", "sleep_quality", "steps", "floors_climbed",
    "dsa_tutorials", "gate_tutorials", "gate_homework",
    "verbal_practice_mins", "revision_mins", "coding_tasks",
    "clean_eating", "supplements", "oats_consumed", "calorie_deficit",
    "sleep_on_time",
    "prev_productivity",  # lag-1 feature
    "rolling_avg_7d",     # rolling mean of last 7 days
]


def _build_features(entries):
    """Convert list of DayEntry → numpy feature matrix X and target vector y."""
    from core import DayEntry
    scores = [e.productivity_score for e in entries]

    X, y = [], []
    for i, e in enumerate(entries[1:], start=1):
        prev_prod = scores[i - 1]
        window    = scores[max(0, i - 7): i]
        roll_avg  = sum(window) / len(window)

        row = [
            e.sleep_hours, e.sleep_quality, e.steps, e.floors_climbed,
            e.dsa_tutorials, e.gate_tutorials, e.gate_homework,
            e.verbal_practice_mins, e.revision_mins, e.coding_tasks,
            e.clean_eating, e.supplements, e.oats_consumed, e.calorie_deficit,
            e.sleep_on_time, prev_prod, roll_avg,
        ]
        X.append(row)
        y.append(e.productivity_score)

    return np.array(X), np.array(y)


def train(entries) -> dict:
    """Train RF + GB models. Returns evaluation metrics."""
    if len(entries) < 14:
        return {"error": "Need at least 14 days of data to train."}

    try:
        from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
        from sklearn.model_selection import cross_val_score
        from sklearn.preprocessing import StandardScaler
    except ImportError:
        return {"error": "scikit-learn not installed. Run: pip install scikit-learn"}

    X, y = _build_features(entries)

    # Train/test split: last 20% as test
    split = max(1, int(len(X) * 0.8))
    X_tr, X_te = X[:split], X[split:]
    y_tr, y_te = y[:split], y[split:]

    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_tr)
    X_te_s = scaler.transform(X_te)

    rf = RandomForestRegressor(n_estimators=200, max_depth=6, random_state=42)
    gb = GradientBoostingRegressor(n_estimators=200, max_depth=4, learning_rate=0.05, random_state=42)

    rf.fit(X_tr_s, y_tr)
    gb.fit(X_tr_s, y_tr)

    def rmse(pred, true):
        return float(np.sqrt(np.mean((pred - true) ** 2)))

    rf_rmse = rmse(rf.predict(X_te_s), y_te)
    gb_rmse = rmse(gb.predict(X_te_s), y_te)

    # Feature importances (RF)
    importances = sorted(
        zip(FEATURES, rf.feature_importances_),
        key=lambda x: x[1], reverse=True
    )

    # Persist
    with open(RF_PATH, "wb") as f:  pickle.dump((rf, scaler), f)
    with open(GB_PATH, "wb") as f:  pickle.dump((gb, scaler), f)

    meta = {
        "trained_on": len(entries),
        "rf_rmse": round(rf_rmse, 2),
        "gb_rmse": round(gb_rmse, 2),
        "top_features": importances[:5],
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    return meta


def predict_tomorrow(entries) -> dict:
    """Predict tomorrow's productivity score using last entry as input."""
    if not RF_PATH.exists():
        return {"error": "Model not trained yet. Run train() first."}

    with open(RF_PATH, "rb") as f:
        rf, scaler = pickle.load(f)
    with open(GB_PATH, "rb") as f:
        gb, _ = pickle.load(f)

    scores = [e.productivity_score for e in entries]
    last   = entries[-1]
    roll   = sum(scores[-7:]) / len(scores[-7:])

    row = np.array([[
        last.sleep_hours, last.sleep_quality, last.steps, last.floors_climbed,
        last.dsa_tutorials, last.gate_tutorials, last.gate_homework,
        last.verbal_practice_mins, last.revision_mins, last.coding_tasks,
        last.clean_eating, last.supplements, last.oats_consumed, last.calorie_deficit,
        last.sleep_on_time, last.productivity_score, roll,
    ]])

    row_s = scaler.transform(row)
    rf_pred = float(rf.predict(row_s)[0])
    gb_pred = float(gb.predict(row_s)[0])
    ensemble = (rf_pred + gb_pred) / 2

    return {
        "random_forest":  round(min(100, max(0, rf_pred)), 1),
        "gradient_boost": round(min(100, max(0, gb_pred)), 1),
        "ensemble":       round(min(100, max(0, ensemble)), 1),
    }


def get_model_meta() -> dict:
    if META_PATH.exists():
        with open(META_PATH) as f:
            return json.load(f)
    return {}
