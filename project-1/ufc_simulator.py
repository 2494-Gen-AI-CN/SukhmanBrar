"""
Basic UFC Fight Simulator

Loads fighter statistics from fighter.csv and simulates a matchup between
two fighters, predicting a winner and printing a brief summary.

Usage:
    python ufc_simulator.py
"""

import csv
import math
import os
from difflib import get_close_matches

FIGHTER_CSV = os.path.join(os.path.dirname(__file__), "fighter.csv")


def load_fighters(path=FIGHTER_CSV):
    """Load all fighters from the CSV into a dict keyed by fighter_name."""
    fighters = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("fighter_name") or "").strip()
            if not name:
                continue
            fighters[name.lower()] = {
                "id": row.get("fighter_id", "").strip(),
                "name": name,
                "nick_name": (row.get("fighter_nick_name") or "").strip(),
                "height": (row.get("height") or "").strip(),
                "weight_lbs": _to_float(row.get("weight_lbs")),
                "reach_inches": _to_float(row.get("reach_inches")),
                "stance": (row.get("stance") or "").strip(),
                "dob": (row.get("dob") or "").strip(),
                "slpm": _to_float(row.get("slpm")),
                "str_acc": _to_float(row.get("str_acc")),
                "sapm": _to_float(row.get("sapm")),
                "str_def": _to_float(row.get("str_def")),
                "td_avg": _to_float(row.get("td_avg")),
                "td_acc": _to_float(row.get("td_acc")),
                "td_def": _to_float(row.get("td_def")),
                "sub_avg": _to_float(row.get("sub_avg")),
            }
    return fighters


def _to_float(value):
    """Safely convert a value to float, returning 0.0 on failure."""
    try:
        if value is None or str(value).strip() == "":
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def find_fighter(fighters, query):
    """Find a fighter by name, with fuzzy fallback."""
    q = query.strip().lower()
    if q in fighters:
        return fighters[q]
    # Try close matches
    matches = get_close_matches(q, fighters.keys(), n=1, cutoff=0.7)
    if matches:
        return fighters[matches[0]]
    return None


def compute_score(f):
    """
    Compute a composite fighter score from 0-100.

    Weights:
      - Striking (40%): SLpM offense * accuracy * defense
      - Grappling (30%): Takedown offense * accuracy * defense
      - Submissions (15%): Submission average
      - Physical/Tale of the tape (15%): Reach, weight, stance versatility
    """
    slpm = f["slpm"]
    str_acc = f["str_acc"] / 100.0
    str_def = f["str_def"] / 100.0
    td_avg = f["td_avg"]
    td_acc = f["td_acc"] / 100.0
    td_def = f["td_def"] / 100.0
    sub_avg = f["sub_avg"]
    reach = f["reach_inches"]
    weight = f["weight_lbs"]

    striking = slpm * str_acc * str_def
    grappling = td_avg * td_acc * td_def
    submissions = sub_avg
    physical = (reach / 80.0) * 5 + (weight / 200.0) * 5  # scaled 0-10 roughly

    # Normalize each component roughly to a 0-10 scale using log-ish scaling
    def norm(x, scale=10.0):
        return min(x * scale, scale)

    score = (
        0.40 * norm(striking)
        + 0.30 * norm(grappling)
        + 0.15 * norm(submissions, scale=50.0)
        + 0.15 * norm(physical)
    )
    return min(max(score, 0.0), 100.0)


def predict_winner(f1, f2):
    """Return (winner_dict, loser_dict, win_probability_percent)."""
    s1 = compute_score(f1)
    s2 = compute_score(f2)

    # Convert scores into a win probability using a softmax-like curve
    diff = s1 - s2
    # Logistic function maps score difference to probability
    prob = 1.0 / (1.0 + math.exp(-diff / 6.0))
    prob_percent = prob * 100.0

    if prob_percent >= 50.0:
        return f1, f2, prob_percent
    else:
        return f2, f1, 100.0 - prob_percent


def summary(winner, loser, prob):
    """Build a brief text summary of the matchup."""
    lines = []
    lines.append(f"Predicted Winner: {winner['name']}")
    if winner.get("nick_name"):
        lines.append(f"Nickname: {winner['nick_name']}")
    lines.append(f"Win Probability: {prob:.1f}%")
    lines.append("")
    lines.append("Tale of the tape:")
    lines.append(f"  {winner['name']}:  {winner['height']}, {winner['weight_lbs']} lbs, "
                 f"Reach {winner['reach_inches']}\", {winner['stance']}")
    lines.append(f"  {loser['name']}:  {loser['height']}, {loser['weight_lbs']} lbs, "
                 f"Reach {loser['reach_inches']}\", {loser['stance']}")
    lines.append("")
    lines.append("Key stats:")

    w_score = compute_score(winner)
    l_score = compute_score(loser)

    lines.append(f"  {winner['name']} composite score: {w_score:.1f}/100")
    lines.append(f"  {loser['name']} composite score: {l_score:.1f}/100")
    lines.append("")

    # Highlight advantages
    adv = []
    if winner["slpm"] > loser["slpm"]:
        adv.append(f"{winner['name']} lands more strikes per minute "
                   f"({winner['slpm']} vs {loser['slpm']})")
    if winner["str_def"] > loser["str_def"]:
        adv.append(f"{winner['name']} has better striking defense "
                   f"({winner['str_def']}% vs {loser['str_def']}%)")
    if winner["td_avg"] > loser["td_avg"]:
        adv.append(f"{winner['name']} averages more takedowns "
                   f"({winner['td_avg']} vs {loser['td_avg']})")
    if winner["td_def"] > loser["td_def"]:
        adv.append(f"{winner['name']} defends takedowns better "
                   f"({winner['td_def']}% vs {loser['td_def']}%)")
    if winner["sub_avg"] > loser["sub_avg"]:
        adv.append(f"{winner['name']} has a higher submission rate "
                   f"({winner['sub_avg']} vs {loser['sub_avg']})")
    if winner["reach_inches"] and loser["reach_inches"] and winner["reach_inches"] > loser["reach_inches"]:
        adv.append(f"{winner['name']} has a {winner['reach_inches'] - loser['reach_inches']:.0f}\" reach advantage")

    if adv:
        lines.append("Advantages:")
        for a in adv:
            lines.append(f"  - {a}")
    else:
        lines.append("This is a closely matched fight with no clear statistical edge.")

    return "\n".join(lines)


def list_fighters(fighters, limit=20):
    """Print a numbered sample of available fighters."""
    names = sorted(fighters.keys())
    print("\nAvailable fighters (showing first {}):".format(limit))
    for i, key in enumerate(names[:limit], 1):
        f = fighters[key]
        print(f"  {i}. {f['name']}")


def main():
    print("=== UFC Fight Simulator ===\n")

    if not os.path.exists(FIGHTER_CSV):
        print(f"Error: {FIGHTER_CSV} not found.")
        print("Place fighter.csv in this directory and try again.")
        return

    fighters = load_fighters()
    print(f"Loaded {len(fighters)} fighters.\n")

    list_fighters(fighters)

    print("\nEnter two fighters to simulate.")
    name1 = input("Fighter 1: ").strip()
    name2 = input("Fighter 2: ").strip()

    f1 = find_fighter(fighters, name1)
    f2 = find_fighter(fighters, name2)

    if not f1:
        print(f"\nCould not find fighter: {name1}")
        return
    if not f2:
        print(f"\nCould not find fighter: {name2}")
        return
    if f1["name"].lower() == f2["name"].lower():
        print("\nA fighter cannot fight themselves.")
        return

    print("\n" + "=" * 45)
    print(f"MATCHUP: {f1['name']} vs {f2['name']}")
    print("=" * 45 + "\n")

    winner, loser, prob = predict_winner(f1, f2)
    print(summary(winner, loser, prob))


if __name__ == "__main__":
    main()
