"""
UFC Fight Simulator — Streamlit Frontend

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
import math
from difflib import get_close_matches
import os

FIGHTER_CSV = os.path.join(os.path.dirname(__file__), "fighter.csv")


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
@st.cache_data
def load_fighters(path=FIGHTER_CSV):
    fighters = {}
    if not os.path.exists(path):
        return fighters
    df = pd.read_csv(path)
    for _, row in df.iterrows():
        name = str(row.get("fighter_name", "")).strip()
        if not name or name == "nan":
            continue
        fighters[name.lower()] = {
            "id": str(row.get("fighter_id", "")).strip(),
            "name": name,
            "nick_name": str(row.get("fighter_nick_name", "")).strip(),
            "height": str(row.get("height", "")).strip(),
            "weight_lbs": _to_float(row.get("weight_lbs")),
            "reach_inches": _to_float(row.get("reach_inches")),
            "stance": str(row.get("stance", "")).strip(),
            "dob": str(row.get("dob", "")).strip(),
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
    try:
        if value is None or str(value).strip() == "" or str(value).strip().lower() == "nan":
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def find_fighter(fighters, query):
    q = query.strip().lower()
    if q in fighters:
        return fighters[q]
    matches = get_close_matches(q, fighters.keys(), n=1, cutoff=0.7)
    if matches:
        return fighters[matches[0]]
    return None


def compute_score(f):
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
    physical = (reach / 80.0) * 5 + (weight / 200.0) * 5

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
    s1 = compute_score(f1)
    s2 = compute_score(f2)
    diff = s1 - s2
    prob = 1.0 / (1.0 + math.exp(-diff / 6.0))
    prob_percent = prob * 100.0
    if prob_percent >= 50.0:
        return f1, f2, prob_percent, s1, s2
    else:
        return f2, f1, 100.0 - prob_percent, s2, s1


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="UFC Fight Simulator",
    page_icon="\U0001F947",
    layout="wide",
)

st.title("\U0001F947 UFC Fight Simulator")
st.caption("Predict the winner between two UFC fighters based on career statistics.")

fighters = load_fighters()

if not fighters:
    st.error(f"`fighter.csv` not found or empty. Place it in `{os.path.dirname(__file__)}`.")
    st.stop()

name_options = sorted(fighters.values(), key=lambda f: f["name"])
name_labels = [f["name"] for f in name_options]

col1, col2 = st.columns(2)
with col1:
    f1_label = st.selectbox("Fighter 1", name_labels, index=0)
with col2:
    default_idx = 1 if len(name_labels) > 1 else 0
    f2_label = st.selectbox("Fighter 2", name_labels, index=default_idx)

f1 = next(f for f in name_options if f["name"] == f1_label)
f2 = next(f for f in name_options if f["name"] == f2_label)

if f1["name"].lower() == f2["name"].lower():
    st.warning("Pick two different fighters.")
    st.stop()

winner, loser, prob, w_score, l_score = predict_winner(f1, f2)

# Divider
st.markdown("---")

# Result header
st.subheader(f"\u270A {winner['name']} vs {loser['name']}")
if winner.get("nick_name") and winner["nick_name"] != "nan":
    st.caption(f"{winner['name']} \"{winner['nick_name']}\"")

# Probability banner
prob_color = "#10b981" if prob >= 60 else "#f59e0b" if prob >= 55 else "#ef4444"
st.markdown(
    f"""
    <div style="
        background: linear-gradient(90deg, {prob_color}22, {prob_color}44);
        border-left: 6px solid {prob_color};
        padding: 1rem 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
    ">
        <h2 style="margin:0; color:{prob_color};">
            Predicted Winner: <b>{winner['name']}</b>
        </h2>
        <p style="margin:0.5rem 0 0 0; font-size:1.25rem;">
            Win Probability: <b>{prob:.1f}%</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Composite scores
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(f"{winner['name']} Score", f"{w_score:.1f} / 100")
with c2:
    st.metric(f"{loser['name']} Score", f"{l_score:.1f} / 100")
with c3:
    st.metric("Score Differential", f"{abs(w_score - l_score):.1f}")

st.markdown("---")

# Tale of the tape
st.subheader("Tale of the Tape")
tt_col1, tt_col2 = st.columns(2)
with tt_col1:
    st.markdown(f"### {winner['name']}")
    st.write(f"**Height:** {winner['height'] or 'N/A'}")
    st.write(f"**Weight:** {winner['weight_lbs']:.0f} lbs" if winner["weight_lbs"] else "**Weight:** N/A")
    st.write(f"**Reach:** {winner['reach_inches']:.0f}\"" if winner["reach_inches"] else "**Reach:** N/A")
    st.write(f"**Stance:** {winner['stance'] or 'N/A'}")
with tt_col2:
    st.markdown(f"### {loser['name']}")
    st.write(f"**Height:** {loser['height'] or 'N/A'}")
    st.write(f"**Weight:** {loser['weight_lbs']:.0f} lbs" if loser["weight_lbs"] else "**Weight:** N/A")
    st.write(f"**Reach:** {loser['reach_inches']:.0f}\"" if loser["reach_inches"] else "**Reach:** N/A")
    st.write(f"**Stance:** {loser['stance'] or 'N/A'}")

st.markdown("---")

# Key stats comparison
st.subheader("Key Stats Comparison")

stats = [
    ("SLpM (Strikes Landed/Min)", "slpm", "higher is better"),
    ("Str. Acc. (%)", "str_acc", "higher is better"),
    ("Str. Def. (%)", "str_def", "higher is better"),
    ("SApM (Strikes Absorbed/Min)", "sapm", "lower is better"),
    ("Takedown Avg", "td_avg", "higher is better"),
    ("Takedown Acc. (%)", "td_acc", "higher is better"),
    ("Takedown Def. (%)", "td_def", "higher is better"),
    ("Submission Avg", "sub_avg", "higher is better"),
]

comp_data = []
for label, key, direction in stats:
    v1 = f1[key]
    v2 = f2[key]
    comp_data.append({
        "Stat": label,
        f1["name"]: v1,
        f2["name"]: v2,
        "Direction": direction,
    })

comp_df = pd.DataFrame(comp_data)
st.dataframe(
    comp_df,
    width="stretch",
    hide_index=True,
    column_config={
        f1["name"]: st.column_config.NumberColumn(format="%.2f"),
        f2["name"]: st.column_config.NumberColumn(format="%.2f"),
    },
)

st.markdown("---")

# Advantages
st.subheader("Matchup Advantages")

advantages = []
if winner["slpm"] > loser["slpm"]:
    advantages.append(f"{winner['name']} lands more strikes per minute ({winner['slpm']:.2f} vs {loser['slpm']:.2f})")
if winner["str_def"] > loser["str_def"]:
    advantages.append(f"{winner['name']} has better striking defense ({winner['str_def']:.0f}% vs {loser['str_def']:.0f}%)")
if winner["td_avg"] > loser["td_avg"]:
    advantages.append(f"{winner['name']} averages more takedowns ({winner['td_avg']:.2f} vs {loser['td_avg']:.2f})")
if winner["td_def"] > loser["td_def"]:
    advantages.append(f"{winner['name']} defends takedowns better ({winner['td_def']:.0f}% vs {loser['td_def']:.0f}%)")
if winner["sub_avg"] > loser["sub_avg"]:
    advantages.append(f"{winner['name']} has a higher submission rate ({winner['sub_avg']:.2f} vs {loser['sub_avg']:.2f})")
if winner["reach_inches"] and loser["reach_inches"] and winner["reach_inches"] > loser["reach_inches"]:
    advantages.append(f"{winner['name']} has a {winner['reach_inches'] - loser['reach_inches']:.0f}\" reach advantage")

if advantages:
    for a in advantages:
        st.success(f"\u2705 {a}")
else:
    st.info("This is a closely matched fight with no clear statistical edge.")

st.markdown("---")
st.caption(
    "Scores are a composite of striking, grappling, submission, and physical attributes. "
    "This is a statistical simulation, not a guarantee of real-world outcomes."
)
