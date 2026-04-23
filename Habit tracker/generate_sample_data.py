"""Generate 90 days of realistic sample data for demo/testing."""

import random
import csv
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)
CSV_PATH = DATA_DIR / "habit_log.csv"

FIELDS = [
    "date","dsa_tutorials","gate_tutorials","gate_homework",
    "verbal_practice_mins","clean_eating","steps","floors_climbed",
    "coding_tasks","sleep_hours","sleep_on_time","supplements",
    "oats_consumed","calorie_deficit","sleep_quality","revision_mins",
    "learning_score","health_score","productivity_score","consistency_index",
]

def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))

def make_entry(d: date, momentum: float) -> dict:
    # momentum 0-1 simulates "good phase" vs "rough phase"
    m = momentum
    dsa  = random.choices([0,1,2,3], weights=[0.2-m*0.1, 0.4, 0.3+m*0.1, m*0.1+0.05])[0]
    gate = random.choices([0,1,2,3], weights=[0.2-m*0.1, 0.4, 0.3+m*0.1, m*0.1+0.05])[0]
    hw   = random.choices([0,1],     weights=[0.3-m*0.2, 0.7+m*0.2])[0]
    verbal = random.choices([0,15,30,45,60], weights=[0.2, 0.2, 0.3, 0.2, 0.1])[0] if m > 0.3 else random.choices([0,15,30], weights=[0.5,0.3,0.2])[0]
    rev  = int(random.gauss(45 + m*30, 15))
    rev  = max(0, min(120, rev))
    code = random.choices([0,1,2,3,4,5], weights=[0.1, 0.15, 0.25, 0.25+m*0.1, 0.15, 0.1])[0]
    steps = int(random.gauss(8000 + m*4000, 2500))
    steps = max(0, min(20000, steps))
    floors = random.choices([0,2,4,6,8,10,12], weights=[0.1,0.1,0.15,0.2,0.2,0.15,0.1])[0]
    sleep_h = round(random.gauss(6.5 + m*1.2, 0.8), 1)
    sleep_h = max(4, min(10, sleep_h))
    sq  = random.choices([0,1,2], weights=[0.15-m*0.05, 0.45, 0.4+m*0.05])[0]
    clean = 1 if random.random() < (0.4 + m*0.4) else 0
    on_time = 1 if random.random() < (0.5 + m*0.3) else 0
    supp = 1 if random.random() < (0.5 + m*0.3) else 0
    oats = 1 if random.random() < (0.4 + m*0.4) else 0
    cal  = 1 if random.random() < (0.4 + m*0.4) else 0

    # Scores
    learn = clamp(
        min(dsa/2,1)*25 + min(gate/2,1)*20 + hw*15 +
        min(verbal/30,1)*15 + min(rev/60,1)*25
    )
    health = clamp(
        min(steps/12000,1)*25 + min(floors/10,1)*10 +
        min(sleep_h/7.5,1)*25 + (sq/2)*15 +
        clean*10 + supp*5 + oats*5 + cal*5
    )
    prod = clamp(min(code/3,1)*40 + learn*0.4 + health*0.2)

    return {
        "date": d.isoformat(),
        "dsa_tutorials": dsa,
        "gate_tutorials": gate,
        "gate_homework": hw,
        "verbal_practice_mins": verbal,
        "clean_eating": clean,
        "steps": steps,
        "floors_climbed": floors,
        "coding_tasks": code,
        "sleep_hours": sleep_h,
        "sleep_on_time": on_time,
        "supplements": supp,
        "oats_consumed": oats,
        "calorie_deficit": cal,
        "sleep_quality": sq,
        "revision_mins": rev,
        "learning_score": round(learn, 2),
        "health_score": round(health, 2),
        "productivity_score": round(prod, 2),
        "consistency_index": 0,
    }

def generate(days=90):
    start = date.today() - timedelta(days=days-1)
    rows = []
    # Simulate phases: rough start → improvement → plateau → another dip → recovery
    for i in range(days):
        if i < 20:
            m = 0.3 + i * 0.015
        elif i < 45:
            m = 0.6 + (i-20) * 0.008
        elif i < 60:
            m = 0.8 - (i-45) * 0.025
        else:
            m = 0.4 + (i-60) * 0.012
        m = max(0.1, min(0.95, m + random.gauss(0, 0.05)))
        rows.append(make_entry(start + timedelta(days=i), m))

    # Compute consistency index (7-day rolling avg - std)
    scores = [r["productivity_score"] for r in rows]
    for i, row in enumerate(rows):
        w = scores[max(0, i-6): i+1]
        avg = sum(w) / len(w)
        std = (sum((x-avg)**2 for x in w)/len(w))**0.5 if len(w)>1 else 0
        row["consistency_index"] = round(clamp(avg - std), 2)

    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {days} days of sample data → {CSV_PATH}")

if __name__ == "__main__":
    generate()
