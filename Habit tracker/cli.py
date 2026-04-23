#!/usr/bin/env python3
"""
Daily input CLI for the Personal Productivity, Health & Learning Analytics System.
Run: python cli.py
"""

import sys
from datetime import date
from core import (
    DayEntry, compute_scores, save_entry, entry_exists,
    generate_recommendations, generate_alerts, load_entries,
    get_streaks, TARGETS
)

# ── Terminal helpers ──────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
BLUE   = "\033[34m"

def color(text, c): return f"{c}{text}{RESET}"
def header(text):   print(f"\n{BOLD}{CYAN}{'─'*56}{RESET}\n  {BOLD}{text}{RESET}\n{BOLD}{CYAN}{'─'*56}{RESET}")
def section(text):  print(f"\n{BOLD}{BLUE}▸ {text}{RESET}")
def ok(text):       print(color(f"  ✓ {text}", GREEN))
def warn(text):     print(color(f"  ⚠ {text}", YELLOW))
def err(text):      print(color(f"  ✗ {text}", RED))


def ask_int(prompt, default=0, min_val=0, max_val=999) -> int:
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = int(raw)
            if min_val <= val <= max_val:
                return val
            warn(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            warn("Enter a whole number.")


def ask_float(prompt, default=7.5, min_val=0.0, max_val=24.0) -> float:
    while True:
        raw = input(f"  {prompt} [{default}]: ").strip()
        if raw == "":
            return default
        try:
            val = float(raw)
            if min_val <= val <= max_val:
                return val
            warn(f"Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            warn("Enter a decimal number (e.g. 7.5).")


def ask_yes_no(prompt, default=True) -> int:
    default_str = "Y/n" if default else "y/N"
    while True:
        raw = input(f"  {prompt} [{default_str}]: ").strip().lower()
        if raw == "":
            return 1 if default else 0
        if raw in ("y", "yes"):
            return 1
        if raw in ("n", "no"):
            return 0
        warn("Enter y or n.")


def ask_quality(prompt) -> int:
    mapping = {"good": 2, "average": 1, "poor": 0, "g": 2, "a": 1, "p": 0}
    while True:
        raw = input(f"  {prompt} [good/average/poor]: ").strip().lower()
        if raw in mapping:
            return mapping[raw]
        warn("Enter good, average, or poor.")


# ── Score display ─────────────────────────────────────────────────────────────

def score_bar(score: float, width: int = 30) -> str:
    filled = int(score / 100 * width)
    bar = "█" * filled + "░" * (width - filled)
    if score >= 75:
        c = GREEN
    elif score >= 50:
        c = YELLOW
    else:
        c = RED
    return f"{c}[{bar}]{RESET} {score:.1f}"


def display_scores(entry: DayEntry):
    section("Today's scores")
    print(f"  Learning score      {score_bar(entry.learning_score)}")
    print(f"  Health score        {score_bar(entry.health_score)}")
    print(f"  Productivity score  {score_bar(entry.productivity_score)}")
    print(f"  Consistency index   {score_bar(entry.consistency_index)}")


# ── Main input flow ───────────────────────────────────────────────────────────

def log_today():
    today = date.today().isoformat()
    header(f"Daily Log — {today}")

    if entry_exists(today):
        warn(f"An entry for {today} already exists.")
        overwrite = ask_yes_no("Overwrite it?", default=False)
        if not overwrite:
            print("  Keeping existing entry. Bye!")
            return

    entry = DayEntry(date=today)

    # ── Learning ──
    section("Learning")
    entry.dsa_tutorials       = ask_int("DSA tutorials completed", 0, 0, 20)
    entry.gate_tutorials      = ask_int("GATE tutorials watched",  0, 0, 20)
    entry.gate_homework       = ask_int("GATE homework completed", 0, 0, 10)
    entry.verbal_practice_mins= ask_int("Verbal aptitude practice (mins)", 0, 0, 180)
    entry.revision_mins       = ask_int("Revision time GATE + DSA (mins)", 0, 0, 480)

    # ── Coding ──
    section("Coding")
    entry.coding_tasks        = ask_int("Coding tasks completed", 0, 0, 50)

    # ── Health ──
    section("Health")
    entry.steps               = ask_int("Steps walked", 0, 0, 100_000)
    entry.floors_climbed      = ask_int("Floors climbed", 0, 0, 200)
    entry.clean_eating        = ask_yes_no("Clean eating today?")
    entry.calorie_deficit     = ask_yes_no("Calorie deficit maintained?")
    entry.oats_consumed       = ask_yes_no("Oats consumed?")
    entry.supplements         = ask_yes_no("Supplements taken?")

    # ── Sleep ──
    section("Sleep")
    entry.sleep_hours         = ask_float("Sleep duration (hours)", 7.5, 0, 24)
    entry.sleep_on_time       = ask_yes_no("Slept on time?")
    entry.sleep_quality       = ask_quality("Sleep quality")

    # ── Compute ──
    entry = compute_scores(entry)
    all_entries = load_entries()
    # Replace last entry if same date, then recompute consistency
    all_entries = [e for e in all_entries if e.date != today]
    all_entries.append(entry)
    from core import compute_consistency
    all_entries = compute_consistency(all_entries)
    entry = all_entries[-1]

    # ── Save ──
    # Remove old CSV row for today if it exists, then append
    _rewrite_csv(all_entries)

    # ── Display ──
    display_scores(entry)

    # ── Goal deltas ──
    section("Goal progress")
    _print_goal("Steps",   entry.steps,       TARGETS["steps"],       "steps")
    _print_goal("Floors",  entry.floors_climbed, TARGETS["floors_climbed"], "floors")
    _print_goal("Sleep",   entry.sleep_hours,  TARGETS["sleep_hours"], "h")
    _print_goal("Revision",entry.revision_mins, TARGETS["revision_mins"], " min")
    _print_goal("Coding",  entry.coding_tasks, TARGETS["coding_tasks"], " tasks")

    # ── Streaks ──
    streaks = get_streaks(all_entries)
    section("Streaks")
    print(f"  Current streak : {BOLD}{streaks['current']}{RESET} day(s)")
    print(f"  Best streak    : {BOLD}{streaks['best']}{RESET} day(s)")

    # ── Alerts ──
    alerts = generate_alerts(all_entries)
    if alerts:
        section("Alerts")
        for a in alerts:
            warn(a)

    # ── Recommendations ──
    recs = generate_recommendations(all_entries)
    section("Recommendations")
    for r in recs:
        ok(r)

    print(f"\n{BOLD}Entry saved for {today}.{RESET} Run `python dashboard.py` to view your full analytics.\n")


def _print_goal(label, actual, target, unit):
    pct = min(actual / target * 100, 100) if target else 0
    status = "✓" if pct >= 100 else "·"
    c = GREEN if pct >= 100 else (YELLOW if pct >= 60 else RED)
    print(f"  {color(status, c)} {label:<12} {actual}{unit} / {target}{unit}  ({pct:.0f}%)")


def _rewrite_csv(entries):
    from core import CSV_PATH, FIELDS
    import csv
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        for e in entries:
            writer.writerow({k: getattr(e, k, "") for k in FIELDS})


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    try:
        log_today()
    except KeyboardInterrupt:
        print("\n\nAborted. Nothing was saved.")
        sys.exit(0)
