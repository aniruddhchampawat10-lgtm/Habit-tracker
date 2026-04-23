"""
Personal Productivity, Health & Learning Analytics Dashboard
Run: streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import date, timedelta
from pathlib import Path


def hex_to_rgba(hex_color, alpha=0.07):
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"
# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Productivity Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Import local modules ──────────────────────────────────────────────────────
import sys
sys.path.insert(0, str(Path(__file__).parent))
from core import (
    load_entries, get_streaks,
    generate_recommendations, generate_alerts, TARGETS
)
from ml_model import train, predict_tomorrow, get_model_meta

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .metric-card {
    background: #1e1e2e;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    border: 1px solid #2a2a3e;
  }
  .score-good  { color: #4ade80; }
  .score-avg   { color: #fbbf24; }
  .score-poor  { color: #f87171; }
  div[data-testid="metric-container"] {
    background: rgba(255,255,255,0.04);
    border-radius: 10px;
    padding: 0.5rem 1rem;
    border: 1px solid rgba(255,255,255,0.08);
  }
</style>
""", unsafe_allow_html=True)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=30)
def get_data():
    entries = load_entries()
    if not entries:
        return pd.DataFrame()
    rows = []
    for e in entries:
        rows.append({
            "date": e.date,
            "dsa_tutorials": e.dsa_tutorials,
            "gate_tutorials": e.gate_tutorials,
            "gate_homework": e.gate_homework,
            "verbal_practice_mins": e.verbal_practice_mins,
            "clean_eating": e.clean_eating,
            "steps": e.steps,
            "floors_climbed": e.floors_climbed,
            "coding_tasks": e.coding_tasks,
            "sleep_hours": e.sleep_hours,
            "sleep_on_time": e.sleep_on_time,
            "supplements": e.supplements,
            "oats_consumed": e.oats_consumed,
            "calorie_deficit": e.calorie_deficit,
            "sleep_quality": e.sleep_quality,
            "revision_mins": e.revision_mins,
            "learning_score": e.learning_score,
            "health_score": e.health_score,
            "productivity_score": e.productivity_score,
            "consistency_index": e.consistency_index,
        })
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)

entries_raw = load_entries()
df = get_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("📊 Analytics")
    st.caption("Personal Productivity System")
    st.divider()

    if df.empty:
        st.warning("No data yet. Run `python cli.py` to log your first day, or `python generate_sample_data.py` for demo data.")
        st.stop()

    view = st.radio("View", ["Dashboard", "Trends", "Correlations", "ML Predictions", "Raw Data"])
    st.divider()

    # Date range filter
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.date_input(
        "Date range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start_d, end_d = date_range
        df = df[(df["date"].dt.date >= start_d) & (df["date"].dt.date <= end_d)]

    st.divider()
    st.caption(f"Total days logged: **{len(df)}**")

# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD VIEW
# ─────────────────────────────────────────────────────────────────────────────
if view == "Dashboard":
    st.title("🏠 Dashboard")

    last  = df.iloc[-1]
    prev  = df.iloc[-2] if len(df) > 1 else last
    streaks = get_streaks(entries_raw)

    # ── KPI row ──
    c1, c2, c3, c4, c5 = st.columns(5)
    def delta(col):
        return float(last[col] - prev[col])

    c1.metric("Productivity",  f"{last['productivity_score']:.1f}",   f"{delta('productivity_score'):+.1f}")
    c2.metric("Learning",      f"{last['learning_score']:.1f}",       f"{delta('learning_score'):+.1f}")
    c3.metric("Health",        f"{last['health_score']:.1f}",         f"{delta('health_score'):+.1f}")
    c4.metric("Current Streak",f"{streaks['current']} days",          f"Best: {streaks['best']}")
    c5.metric("Consistency",   f"{last['consistency_index']:.1f}",    f"{delta('consistency_index'):+.1f}")

    st.divider()

    # ── Score trend sparklines ──
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        for col, color, name in [
            ("productivity_score", "#818cf8", "Productivity"),
            ("learning_score",     "#34d399", "Learning"),
            ("health_score",       "#fb923c", "Health"),
        ]:
            fig.add_trace(go.Scatter(
                x=df["date"], y=df[col],
                name=name, line=dict(color=color, width=2),
                fill="tozeroy",
                fillcolor=hex_to_rgba(color, 0.07),
                #fill="tozeroy", fillcolor=color.replace(")", ",0.07)").replace("rgb","rgba") if "rgb" in color else color + "12",
            ))

        fig.update_layout(
            title="Score trends", height=320,
            legend=dict(orientation="h", y=-0.2),
            xaxis=dict(showgrid=False), yaxis=dict(range=[0,100]),
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc"),
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        # Habit completion radar for last day
        categories = ["DSA","GATE","Homework","Verbal","Coding","Steps","Sleep","Revision"]
        raw_vals = [
            last["dsa_tutorials"]       / TARGETS["dsa_tutorials"],
            last["gate_tutorials"]      / TARGETS["gate_tutorials"],
            last["gate_homework"]       / TARGETS["gate_homework"],
            last["verbal_practice_mins"]/ TARGETS["verbal_practice_mins"],
            last["coding_tasks"]        / TARGETS["coding_tasks"],
            last["steps"]               / TARGETS["steps"],
            last["sleep_hours"]         / TARGETS["sleep_hours"],
            last["revision_mins"]       / TARGETS["revision_mins"],
        ]
        vals = [min(v, 1) * 100 for v in raw_vals]
        vals += [vals[0]]
        cats = categories + [categories[0]]
        fig2 = go.Figure(go.Scatterpolar(
            r=vals, theta=cats,
            fill="toself", line=dict(color="#818cf8"),
            fillcolor="rgba(129,140,248,0.2)",
        ))
        fig2.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0,100])),
            title=f"Today's habit completion — {str(last['date'])[:10]}",
            height=320,
            margin=dict(l=0, r=0, t=40, b=0),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#ccc"),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Alerts & Recommendations ──
    alerts = generate_alerts(entries_raw)
    recs   = generate_recommendations(entries_raw)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("⚠️ Alerts")
        if alerts:
            for a in alerts:
                st.warning(a)
        else:
            st.success("No alerts — keep it up!")
    with col2:
        st.subheader("💡 Recommendations")
        for r in recs:
            st.info(r)

    # ── 7-day habit heatmap ──
    st.subheader("📅 Habit heatmap (last 30 days)")
    recent = df.tail(30).copy()
    habit_cols = [
        "clean_eating","supplements","oats_consumed","calorie_deficit",
        "sleep_on_time","gate_homework",
    ]
    heat_df = recent[["date"] + habit_cols].copy()
    heat_df["date"] = heat_df["date"].dt.strftime("%b %d")
    heat_df = heat_df.set_index("date").T
    fig3 = px.imshow(
        heat_df,
        color_continuous_scale=["#1e1e2e","#34d399"],
        aspect="auto",
        labels=dict(x="Date", y="Habit", color="Done"),
    )
    fig3.update_layout(
        height=240,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#ccc"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig3, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# TRENDS VIEW
# ─────────────────────────────────────────────────────────────────────────────
elif view == "Trends":
    st.title("📈 Trends")

    tab1, tab2, tab3 = st.tabs(["Score trends", "Health metrics", "Learning metrics"])

    with tab1:
        # Weekly rolling average
        df_w = df.copy().set_index("date")
        for col in ["productivity_score","learning_score","health_score"]:
            df_w[f"{col}_7d"] = df_w[col].rolling(7).mean()
        df_w = df_w.reset_index()

        fig = make_subplots(rows=3, cols=1, shared_xaxes=True,
                            subplot_titles=["Productivity","Learning","Health"],
                            vertical_spacing=0.08)
        colors = ["#818cf8","#34d399","#fb923c"]
        for i, (col, c, label) in enumerate([
            ("productivity_score","#818cf8","Productivity"),
            ("learning_score","#34d399","Learning"),
            ("health_score","#fb923c","Health"),
        ], 1):
            fig.add_trace(go.Scatter(x=df_w["date"], y=df_w[col],
                name=label, line=dict(color=c, width=1), opacity=0.4,
                showlegend=False), row=i, col=1)
            fig.add_trace(go.Scatter(x=df_w["date"], y=df_w[f"{col}_7d"],
                name=f"{label} 7d avg", line=dict(color=c, width=2.5),
                showlegend=True), row=i, col=1)
        fig.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                          legend=dict(orientation="h"))
        fig.update_yaxes(range=[0,100])
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        fig = make_subplots(rows=2, cols=2,
            subplot_titles=["Sleep hours","Steps","Floors climbed","Sleep quality"])
        data_pairs = [
            ("sleep_hours", "#60a5fa", TARGETS["sleep_hours"], 1, 1),
            ("steps",        "#34d399", TARGETS["steps"],       1, 2),
            ("floors_climbed","#fb923c",TARGETS["floors_climbed"],2,1),
            ("sleep_quality","#a78bfa", 2,                      2, 2),
        ]
        for col, c, tgt, r, cc in data_pairs:
            fig.add_trace(go.Bar(x=df["date"], y=df[col],
                marker_color=c, name=col, showlegend=False), row=r, col=cc)
            fig.add_hline(y=tgt, line_dash="dot", line_color="white",
                          opacity=0.4, row=r, col=cc)
        fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"))
        st.plotly_chart(fig, use_container_width=True)

    with tab3:
        fig = make_subplots(rows=2, cols=2,
            subplot_titles=["DSA tutorials","GATE tutorials","Revision mins","Coding tasks"])
        for (col, c, tgt, r, cc) in [
            ("dsa_tutorials","#818cf8",TARGETS["dsa_tutorials"],1,1),
            ("gate_tutorials","#34d399",TARGETS["gate_tutorials"],1,2),
            ("revision_mins","#fb923c",TARGETS["revision_mins"],2,1),
            ("coding_tasks","#f472b6",TARGETS["coding_tasks"],2,2),
        ]:
            fig.add_trace(go.Bar(x=df["date"], y=df[col],
                marker_color=c, name=col, showlegend=False), row=r, col=cc)
            fig.add_hline(y=tgt, line_dash="dot", line_color="white",
                          opacity=0.4, row=r, col=cc)
        fig.update_layout(height=500, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"))
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# CORRELATIONS VIEW
# ─────────────────────────────────────────────────────────────────────────────
elif view == "Correlations":
    st.title("🔗 Correlations")

    numeric_cols = [
        "sleep_hours","steps","coding_tasks","revision_mins",
        "verbal_practice_mins","dsa_tutorials","gate_tutorials",
        "clean_eating","supplements","floors_climbed",
        "learning_score","health_score","productivity_score",
    ]
    corr = df[numeric_cols].corr()

    fig = px.imshow(
        corr,
        color_continuous_scale="RdBu",
        zmin=-1, zmax=1,
        text_auto=".2f",
        aspect="auto",
        title="Correlation matrix — all habits vs scores",
    )
    fig.update_layout(height=600, paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#ccc"))
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Sleep vs Productivity")
    fig2 = px.scatter(df, x="sleep_hours", y="productivity_score",
                      color="sleep_quality", size="steps",
                      trendline="ols",
                      color_continuous_scale="Viridis",
                      labels={"sleep_hours":"Sleep (h)","productivity_score":"Productivity"},
                      title="Sleep hours vs Productivity score (bubble = steps)")
    fig2.update_layout(height=420, paper_bgcolor="rgba(0,0,0,0)",
                       plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"))
    st.plotly_chart(fig2, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        fig3 = px.scatter(df, x="steps", y="health_score", trendline="ols",
                          color="clean_eating",
                          title="Steps vs Health score",
                          labels={"steps":"Steps","health_score":"Health score"})
        fig3.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"))
        st.plotly_chart(fig3, use_container_width=True)
    with col2:
        fig4 = px.scatter(df, x="revision_mins", y="learning_score", trendline="ols",
                          color="dsa_tutorials",
                          title="Revision time vs Learning score",
                          labels={"revision_mins":"Revision (min)","learning_score":"Learning score"})
        fig4.update_layout(height=360, paper_bgcolor="rgba(0,0,0,0)",
                           plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"))
        st.plotly_chart(fig4, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# ML PREDICTIONS VIEW
# ─────────────────────────────────────────────────────────────────────────────
elif view == "ML Predictions":
    st.title("🤖 ML Predictions")

    if len(entries_raw) < 14:
        st.warning("You need at least 14 days of data to train the model.")
        st.stop()

    col1, col2 = st.columns([1, 2])

    with col1:
        if st.button("🔁 Train / retrain model", use_container_width=True):
            with st.spinner("Training Random Forest & Gradient Boosting…"):
                meta = train(entries_raw)
            if "error" in meta:
                st.error(meta["error"])
            else:
                st.success("Model trained!")
                st.json(meta)
        else:
            meta = get_model_meta()
            if meta:
                st.info(f"Last trained on {meta.get('trained_on',0)} days")
                st.caption(f"RF RMSE: {meta.get('rf_rmse','—')} | GB RMSE: {meta.get('gb_rmse','—')}")

    with col2:
        preds = predict_tomorrow(entries_raw)
        if "error" in preds:
            st.warning(preds["error"])
        else:
            st.subheader("Tomorrow's predicted productivity")
            p1, p2, p3 = st.columns(3)
            p1.metric("Random Forest",    f"{preds['random_forest']}")
            p2.metric("Gradient Boost",   f"{preds['gradient_boost']}")
            p3.metric("Ensemble",         f"{preds['ensemble']}", delta="best estimate")

            meta = get_model_meta()
            if meta and "top_features" in meta:
                st.subheader("Top predictive features")
                feats = meta["top_features"]
                names = [f[0] for f in feats]
                imps  = [f[1] for f in feats]
                fig = go.Figure(go.Bar(
                    x=imps, y=names,
                    orientation="h",
                    marker_color="#818cf8",
                ))
                fig.update_layout(
                    height=280, yaxis=dict(autorange="reversed"),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#ccc"),
                    margin=dict(l=0,r=0,t=0,b=0),
                )
                st.plotly_chart(fig, use_container_width=True)

    # ── Actual vs predicted chart ──
    st.subheader("Actual vs predicted (last 30 days)")
    preds_list = []
    for i in range(1, min(30, len(entries_raw))):
        p = predict_tomorrow(entries_raw[:i])
        if "ensemble" in p:
            preds_list.append({
                "date": entries_raw[i].date,
                "actual": entries_raw[i].productivity_score,
                "predicted": p["ensemble"],
            })
    if preds_list:
        pred_df = pd.DataFrame(preds_list)
        pred_df["date"] = pd.to_datetime(pred_df["date"])
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=pred_df["date"], y=pred_df["actual"],
            name="Actual", line=dict(color="#34d399", width=2)))
        fig.add_trace(go.Scatter(x=pred_df["date"], y=pred_df["predicted"],
            name="Predicted", line=dict(color="#818cf8", width=2, dash="dot")))
        fig.update_layout(height=320, paper_bgcolor="rgba(0,0,0,0)",
                          plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#ccc"),
                          yaxis=dict(range=[0,100]))
        st.plotly_chart(fig, use_container_width=True)


# ─────────────────────────────────────────────────────────────────────────────
# RAW DATA VIEW
# ─────────────────────────────────────────────────────────────────────────────
elif view == "Raw Data":
    st.title("🗄️ Raw Data")

    st.dataframe(
        df.sort_values("date", ascending=False),
        use_container_width=True,
        height=500,
    )

    csv_bytes = df.to_csv(index=False).encode()
    st.download_button(
        label="⬇️ Download CSV",
        data=csv_bytes,
        file_name=f"habit_log_{date.today().isoformat()}.csv",
        mime="text/csv",
    )

    # ── Weekly summary ──
    st.subheader("Weekly summary")
    df_copy = df.copy()
    df_copy["week"] = df_copy["date"].dt.isocalendar().week
    weekly = df_copy.groupby("week").agg({
        "productivity_score": "mean",
        "learning_score":     "mean",
        "health_score":       "mean",
        "steps":              "mean",
        "sleep_hours":        "mean",
        "coding_tasks":       "sum",
    }).round(1)
    st.dataframe(weekly, use_container_width=True)
