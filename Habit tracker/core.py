"""
Core data models, scoring engine, and analytics for the
Personal Productivity, Health & Learning Analytics System.
"""

import csv
import json
import os
from dataclasses import dataclass, asdict, field
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "habit_log.csv"

# ── Field definitions ─────────────────────────────────────────────────────────

FIELDS = [
    "date",
    "dsa_tutorials",
    "gate_tutorials",
    "gate_homework",
    "verbal_practice_mins",
    "clean_eating",          # 1 / 0
    "steps",
    "floors_climbed",
    "coding_tasks",
    "sleep_hours",
    "sleep_on_time",         # 1 / 0
    "supplements",           # 1 / 0
    "oats_consumed",         # 1 / 0
    "calorie_deficit",       # 1 / 0
    "sleep_quality",         # good=2 average=1 poor=0
    "revision_mins",
    # Computed
    "learning_score",
    "health_score",
    "productivity_score",
    "consistency_index",
]

# ── Data class ────────────────────────────────────────────────────────────────

@dataclass
class DayEntry:
    date: str = ""
    dsa_tutorials: int = 0
    gate_tutorials: int = 0
    gate_homework: int = 0
    verbal_practice_mins: int = 0
    clean_eating: int = 0
    steps: int = 0
    floors_climbed: int = 0
    coding_tasks: int = 0
    sleep_hours: float = 0.0
    sleep_on_time: int = 0
    supplements: int = 0
    oats_consumed: int = 0
    calorie_deficit: int = 0
    sleep_quality: int = 1      # 0=poor 1=average 2=good
    revision_mins: int = 0
    # Computed — filled by scoring engine
    learning_score: float = 0.0
    health_score: float = 0.0
    productivity_score: float = 0.0
    consistency_index: float = 0.0

# ── Scoring engine ────────────────────────────────────────────────────────────

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

def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def compute_scores(e: DayEntry) -> DayEntry:
    """Fill learning_score, health_score, productivity_score, consistency_index."""

    # Learning score (out of 100)
    dsa_pts    = min(e.dsa_tutorials / max(TARGETS["dsa_tutorials"], 1), 1) * 25
    gate_pts   = min(e.gate_tutorials / max(TARGETS["gate_tutorials"], 1), 1) * 20
    hw_pts     = min(e.gate_homework  / max(TARGETS["gate_homework"],  1), 1) * 15
    verbal_pts = min(e.verbal_practice_mins / TARGETS["verbal_practice_mins"], 1) * 15
    rev_pts    = min(e.revision_mins / TARGETS["revision_mins"], 1) * 25
    e.learning_score = _clamp(dsa_pts + gate_pts + hw_pts + verbal_pts + rev_pts)

    # Health score (out of 100)
    steps_pts   = min(e.steps / TARGETS["steps"], 1) * 25
    floors_pts  = min(e.floors_climbed / TARGETS["floors_climbed"], 1) * 10
    sleep_pts   = min(e.sleep_hours / TARGETS["sleep_hours"], 1) * 25
    quality_pts = (e.sleep_quality / 2) * 15        # 0-2 → 0-15
    eating_pts  = e.clean_eating * 10
    supp_pts    = e.supplements * 5
    oats_pts    = e.oats_consumed * 5
    cal_pts     = e.calorie_deficit * 5
    e.health_score = _clamp(
        steps_pts + floors_pts + sleep_pts + quality_pts +
        eating_pts + supp_pts + oats_pts + cal_pts
    )

    # Productivity score — weighted blend
    coding_pts = min(e.coding_tasks / TARGETS["coding_tasks"], 1) * 40
    learn_contrib = e.learning_score * 0.40
    health_contrib = e.health_score * 0.20
    e.productivity_score = _clamp(coding_pts + learn_contrib + health_contrib)

    # Consistency index computed separately (needs history)
    return e


def compute_consistency(entries: list[DayEntry]) -> list[DayEntry]:
    """Add consistency_index to each entry based on 7-day rolling avg."""
    scores = [e.productivity_score for e in entries]
    for i, entry in enumerate(entries):
        window = scores[max(0, i - 6): i + 1]
        if len(window) < 2:
            entry.consistency_index = entry.productivity_score
        else:
            avg = sum(window) / len(window)
            std = (sum((x - avg) ** 2 for x in window) / len(window)) ** 0.5
            entry.consistency_index = _clamp(avg - std)
    return entries

# ── Streak tracking ───────────────────────────────────────────────────────────

def get_streaks(entries: list[DayEntry]) -> dict:
    """Return current streak, best streak, and broken-streak dates."""
    if not entries:
        return {"current": 0, "best": 0, "broken_dates": []}

    threshold = 50.0
    current = 0
    best = 0
    run = 0
    broken = []

    for e in entries:
        if e.productivity_score >= threshold:
            run += 1
            best = max(best, run)
        else:
            if run > 0:
                broken.append(e.date)
            run = 0

    current = run
    return {"current": current, "best": best, "broken_dates": broken[-5:]}

# ── CSV persistence ───────────────────────────────────────────────────────────

def save_entry(entry: DayEntry) -> None:
    exists = CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if not exists:
            writer.writeheader()
        writer.writerow({k: getattr(entry, k, "") for k in FIELDS})


def load_entries() -> list[DayEntry]:
    if not CSV_PATH.exists():
        return []
    entries = []
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            e = DayEntry(
                date=row.get("date", ""),
                dsa_tutorials=int(row.get("dsa_tutorials", 0) or 0),
                gate_tutorials=int(row.get("gate_tutorials", 0) or 0),
                gate_homework=int(row.get("gate_homework", 0) or 0),
                verbal_practice_mins=int(row.get("verbal_practice_mins", 0) or 0),
                clean_eating=int(row.get("clean_eating", 0) or 0),
                steps=int(row.get("steps", 0) or 0),
                floors_climbed=int(row.get("floors_climbed", 0) or 0),
                coding_tasks=int(row.get("coding_tasks", 0) or 0),
                sleep_hours=float(row.get("sleep_hours", 0) or 0),
                sleep_on_time=int(row.get("sleep_on_time", 0) or 0),
                supplements=int(row.get("supplements", 0) or 0),
                oats_consumed=int(row.get("oats_consumed", 0) or 0),
                calorie_deficit=int(row.get("calorie_deficit", 0) or 0),
                sleep_quality=int(row.get("sleep_quality", 1) or 1),
                revision_mins=int(row.get("revision_mins", 0) or 0),
            )
            e = compute_scores(e)
            entries.append(e)
    return compute_consistency(entries)


def entry_exists(date_str: str) -> bool:
    for e in load_entries():
        if e.date == date_str:
            return True
    return False


def get_entry_by_date(date_str: str) -> Optional[DayEntry]:
    for e in load_entries():
        if e.date == date_str:
            return e
    return None

# ── Recommendations ───────────────────────────────────────────────────────────

def generate_recommendations(entries: list[DayEntry]) -> list[str]:
    if not entries:
        return ["Log your first day to get personalised recommendations!"]

    recent = entries[-7:]
    recs = []

    avg_sleep   = sum(e.sleep_hours for e in recent) / len(recent)
    avg_steps   = sum(e.steps for e in recent) / len(recent)
    avg_coding  = sum(e.coding_tasks for e in recent) / len(recent)
    avg_verbal  = sum(e.verbal_practice_mins for e in recent) / len(recent)
    avg_rev     = sum(e.revision_mins for e in recent) / len(recent)
    clean_rate  = sum(e.clean_eating for e in recent) / len(recent)
    supp_rate   = sum(e.supplements for e in recent) / len(recent)

    if avg_sleep < 6.5:
        recs.append(f"Sleep is averaging {avg_sleep:.1f}h — aim for 7.5h. Sleep is your #1 productivity lever.")
    if avg_steps < 8000:
        recs.append(f"Steps averaging {avg_steps:.0f}/day — even a 20-min walk boosts focus significantly.")
    if avg_coding < 2:
        recs.append(f"Coding tasks averaging {avg_coding:.1f}/day — try completing at least 3 tasks daily.")
    if avg_verbal < 20:
        recs.append(f"Verbal practice is low ({avg_verbal:.0f} min/day) — schedule a fixed 30-min slot.")
    if avg_rev < 45:
        recs.append(f"Revision time is {avg_rev:.0f} min/day — increase to 60 min to retain GATE material.")
    if clean_rate < 0.5:
        recs.append("Clean eating below 50% this week — meal prep on Sundays can help consistency.")
    if supp_rate < 0.6:
        recs.append("Supplements missed on most days — keep them next to your alarm/toothbrush.")

    if not recs:
        recs.append("Great week! Maintain your current habits and look to increase your revision time.")

    return recs


# ── Alerts ────────────────────────────────────────────────────────────────────

def generate_alerts(entries: list[DayEntry]) -> list[str]:
    alerts = []
    if len(entries) < 2:
        return alerts

    last = entries[-1]
    prev = entries[-2]

    drop = prev.productivity_score - last.productivity_score
    if drop > 20:
        alerts.append(
            f"Productivity dropped {drop:.0f} pts from {prev.date} to {last.date}. "
            "Check sleep quality and step count."
        )

    streaks = get_streaks(entries)
    if streaks["current"] == 0 and len(entries) >= 2:
        alerts.append("Current streak broken! Start a new one today — even a 60% day counts.")

    if last.sleep_hours < 5.5:
        alerts.append(f"Very low sleep last night ({last.sleep_hours}h). Consider a recovery nap today.")

    return alerts
