import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st
from database import get_connection, init_database

# ---- Initialization --------------------------------------------------------
status = init_database()

st.set_page_config(
    page_title="Road Accident Analytics",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Premium Styling (no divs) ---------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --bg: #0B0F19;
        --panel: #1E293B;
        --text: #F8FAFC;
        --muted: #CBD5E1;
        --accent: #6366F1;
        --line: rgba(148, 163, 184, 0.15);
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: #0F172A;
        border-right: 1px solid var(--line);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 1.2rem !important;
    }

    [data-testid="stMetricLabel"] {
        color: var(--muted) !important;
        font-size: 0.75rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    h1, h2, h3 {
        color: var(--text) !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
        color: white !important;
        font-weight: 700;
        border: none !important;
        border-radius: 10px;
        padding: 0.6rem 1.2rem;
    }

    .stButton > button:hover {
        opacity: 0.9;
    }

    .stTextArea textarea {
        background: #0F172A !important;
        border: 1px solid var(--line) !important;
        color: var(--text) !important;
        border-radius: 10px !important;
    }

    .stSelectSlider, .stMultiSelect, .stSelectbox {
        color: var(--text) !important;
    }

    .stTabs [data-baseweb="tab"] {
        background: transparent;
        color: var(--muted);
        border-bottom: 2px solid transparent;
        border-radius: 0;
    }

    .stTabs [aria-selected="true"] {
        color: var(--text) !important;
        border-bottom-color: #6366F1 !important;
    }

    textarea::placeholder {
        color: var(--muted) !important;
    }

    .stDataFrame {
        background: var(--panel) !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---- Helpers ---------------------------------------------------------------
def run_sql(query: str, params: tuple = ()):
    conn = get_connection()
    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


def build_where(year: str, severities: list, state: str):
    clauses = ["substr(a.date,1,4) = ?"]
    params = [year]
    if severities:
        clauses.append(f"a.severity IN ({','.join(['?'] * len(severities))})")
        params.extend(severities)
    if state and state != "All":
        clauses.append("l.state = ?")
        params.append(state)
    return " AND ".join(clauses), params


# ---- Sidebar (filters only, no KPIs) ---------------------------------------------------------------
with st.sidebar:
    st.title("🚦 Road Accident Analytics")
    st.caption("Analysis Suite")
    st.divider()

    years = run_sql("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y DESC")[
        "y"
    ].tolist()
    year = st.select_slider("Year", options=years, value=years[0] if years else 2024)

    severity_opts = ["Fatal", "Serious", "Minor"]
    severities = st.multiselect(
        "Severity", severity_opts, default=severity_opts
    )

    states = run_sql("SELECT DISTINCT state FROM locations ORDER BY state")[
        "state"
    ].tolist()
    state = st.selectbox("State", ["All"] + states)

    st.divider()
    st.caption(f"✓ Database ready: {status}")

# ---- Top Header (no duplicate KPIs here) ---------------------------------------------------------------
st.title("🚦 Road Accident Analytics")
st.caption("Interactive insights for patterns, hotspots, and severity trends")

# ---- Navigation ---------------------------------------------------------------
nav = st.radio(
    "Navigation",
    ["Overview", "Analytics", "SQL Workspace"],
    horizontal=True,
    label_visibility="collapsed",
)

st.divider()

# ---- OVERVIEW PAGE ---------------------------------------------------------------
if nav == "Overview":
    # KPIs only show here
    metric_df = run_sql(
        """
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN severity='Fatal' THEN 1 ELSE 0 END) AS fatal,
            COALESCE(SUM(num_fatalities), 0) AS deaths,
            (SELECT COUNT(DISTINCT state) FROM locations) AS states
        FROM accidents
        """
    )

    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric(
            "Total Accidents", f"{int(metric_df['total'].iloc[0]):,}"
        )
    with k2:
        st.metric(
            "Fatal Crashes", f"{int(metric_df['fatal'].iloc[0]):,}"
        )
    with k3:
        st.metric(
            "Total Deaths", f"{int(metric_df['deaths'].iloc[0]):,}"
        )
    with k4:
        st.metric(
            "States Covered", f"{int(metric_df['states'].iloc[0]):,}"
        )

    st.divider()

    # Severity breakdown
    where, params = build_where(year, severities, state)
    sev_data = run_sql(
        f"""
        SELECT a.severity, COUNT(*) AS count, SUM(a.num_fatalities) AS deaths
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {where}
        GROUP BY a.severity
        ORDER BY count DESC
        """,
        tuple(params),
    )

    col_a, col_b = st.columns([1.5, 1])

    with col_a:
        st.subheader("Severity Distribution")
        if sev_data.empty:
            st.info("No data for selected filters.")
        else:
            fig = px.bar(
                sev_data,
                x="severity",
                y="count",
                color="severity",
                color_discrete_map={
                    "Fatal": "#ef4444",
                    "Serious": "#f59e0b",
                    "Minor": "#10b981",
                },
                text="count",
            )
            fig.update_layout(
                paper_bgcolor="#0B0F19",
                plot_bgcolor="#0B0F19",
                font_color="#F8FAFC",
                showlegend=False,
                xaxis_title="",
                yaxis_title="",
                margin=dict(l=20, r=20, t=20, b=20),
                height=350,
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.08)")
            st.plotly_chart(fig, use_container_width=True)

    with col_b:
        st.subheader("Summary")
        if sev_data.empty:
            st.caption("No data available.")
        else:
            for _, row in sev_data.iterrows():
                color_map = {
                    "Fatal": "🔴",
                    "Serious": "🟠",
                    "Minor": "🟢",
                }
                st.metric(
                    f"{color_map.get(row['severity'], '')} {row['severity']}",
                    f"{row['count']}",
                    f"Deaths: {row['deaths']}",
                )

    st.divider()

    # 3D, Heatmap, Geo tabs
    tab1, tab2, tab3 = st.tabs(["3D Scatter", "Heatmap", "Geographic Map"])

    with tab1:
        st.subheader("3D Animated Accident Distribution")
        df = run_sql(
            f"""
            SELECT a.date, a.severity, a.num_fatalities, a.num_injuries, a.light_condition,
                   l.latitude, l.longitude, l.state, substr(a.date,1,7) AS month
            FROM accidents a
            JOIN locations l ON a.location_id = l.location_id
            WHERE {where}
            """,
            tuple(params),
        )
        if df.empty:
            st.warning("No data for this filter set.")
        else:
            df["size"] = df["num_injuries"] + 1
            fig = px.scatter_3d(
                df,
                x="longitude",
                y="latitude",
                z="num_fatalities",
                color="severity",
                size="size",
                animation_frame="month",
                color_discrete_map={
                    "Fatal": "#ef4444",
                    "Serious": "#f59e0b",
                    "Minor": "#10b981",
                },
                hover_data=["date", "state", "light_condition"],
                opacity=0.7,
                height=600,
            )
            fig.update_layout(
                scene=dict(
                    xaxis_title="Longitude",
                    yaxis_title="Latitude",
                    zaxis_title="Fatalities",
                    bgcolor="#0B0F19",
                    xaxis=dict(gridcolor="rgba(148,163,184,0.08)"),
                    yaxis=dict(gridcolor="rgba(148,163,184,0.08)"),
                    zaxis=dict(gridcolor="rgba(148,163,184,0.08)"),
                ),
                paper_bgcolor="#0B0F19",
                font_color="#F8FAFC",
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Hour × Day-of-Week Density Heatmap")
        heat = run_sql(
            f"""
            SELECT a.time, a.date
            FROM accidents a
            JOIN locations l ON a.location_id = l.location_id
            WHERE {where}
            """,
            tuple(params),
        )
        if heat.empty:
            st.warning("No data for this filter set.")
        else:
            heat["hour"] = heat["time"].str[:2].astype(int)
            heat["dow"] = pd.to_datetime(heat["date"]).dt.day_name()
            order = [
                "Monday",
                "Tuesday",
                "Wednesday",
                "Thursday",
                "Friday",
                "Saturday",
                "Sunday",
            ]
            pivot = heat.groupby(["dow", "hour"]).size().unstack(fill_value=0)
            pivot = pivot.reindex([d for d in order if d in pivot.index])
            fig = px.imshow(
                pivot,
                aspect="auto",
                color_continuous_scale="Inferno",
                labels=dict(x="Hour of Day", y="Day of Week", color="Accidents"),
                height=500,
            )
            fig.update_layout(
                paper_bgcolor="#0B0F19",
                plot_bgcolor="#0B0F19",
                font_color="#F8FAFC",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.subheader("Geographic Hotspot Map")
        geo = run_sql(
            f"""
            SELECT l.latitude, l.longitude, a.severity, a.num_fatalities, l.state
            FROM accidents a
            JOIN locations l ON a.location_id = l.location_id
            WHERE {where}
            """,
            tuple(params),
        )
        if geo.empty:
            st.warning("No data for this filter set.")
        else:
            fig = px.scatter(
                geo,
                x="longitude",
                y="latitude",
                color="severity",
                size="num_fatalities",
                size_max=22,
                hover_data=["state"],
                color_discrete_map={
                    "Fatal": "#ef4444",
                    "Serious": "#f59e0b",
                    "Minor": "#10b981",
                },
                height=600,
            )
            fig.update_layout(
                paper_bgcolor="#0B0F19",
                plot_bgcolor="#0B0F19",
                font_color="#F8FAFC",
                xaxis=dict(
                    title="Longitude", gridcolor="rgba(148,163,184,0.08)"
                ),
                yaxis=dict(
                    title="Latitude", gridcolor="rgba(148,163,184,0.08)"
                ),
                legend_title_text="Severity",
                margin=dict(l=20, r=20, t=20, b=20),
            )
            st.plotly_chart(fig, use_container_width=True)

# ---- ANALYTICS PAGE ---------------------------------------------------------------
elif nav == "Analytics":
    st.subheader("Accident Trends by Month")
    monthly = run_sql(
        f"""
        SELECT substr(date,1,7) AS month, COUNT(*) AS accidents
        FROM accidents
        WHERE substr(date,1,4) = ?
        GROUP BY substr(date,1,7)
        ORDER BY month
        """,
        (year,),
    )
    if monthly.empty:
        st.info("No monthly trend data available for this year.")
    else:
        fig = px.line(
            monthly,
            x="month",
            y="accidents",
            markers=True,
            title="",
        )
        fig.update_layout(
            paper_bgcolor="#0B0F19",
            plot_bgcolor="#0B0F19",
            font_color="#F8FAFC",
            xaxis_title="Month",
            yaxis_title="Accident Count",
            hovermode="x unified",
            margin=dict(l=20, r=20, t=20, b=20),
            height=450,
        )
        fig.update_xaxes(showgrid=True, gridcolor="rgba(148,163,184,0.08)")
        fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.08)")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("State-wise Accident Count")
    state_data = run_sql(
        """
        SELECT l.state, COUNT(*) AS count
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        GROUP BY l.state
        ORDER BY count DESC
        """
    )
    if state_data.empty:
        st.info("No state data available.")
    else:
        fig = px.bar(
            state_data,
            x="state",
            y="count",
            color="count",
            color_continuous_scale="Viridis",
        )
        fig.update_layout(
            paper_bgcolor="#0B0F19",
            plot_bgcolor="#0B0F19",
            font_color="#F8FAFC",
            xaxis_title="State",
            yaxis_title="Count",
            showlegend=False,
            margin=dict(l=20, r=20, t=20, b=20),
            height=450,
        )
        st.plotly_chart(fig, use_container_width=True)

# ---- SQL WORKSPACE PAGE ---------------------------------------------------------------
elif nav == "SQL Workspace":
    st.subheader("SQL Query Editor")
    sql = st.text_area(
        "Enter your SQLite query:",
        value="SELECT severity, COUNT(*) AS count, SUM(num_fatalities) AS deaths FROM accidents GROUP BY severity ORDER BY count DESC;",
        height=180,
        key="sql_editor",
    )

    col_exec, col_schema = st.columns([3, 1])

    with col_exec:
        if st.button("▶ Execute Query", use_container_width=True):
            try:
                res = run_sql(sql)
                st.session_state["sql_result"] = res
                st.success(f"✓ Query returned {len(res)} rows")
            except Exception as e:
                st.error(f"SQLite error: {str(e)}")

    with col_schema:
        if st.button("Show Schema", use_container_width=False):
            schema = run_sql(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            st.info(
                "Tables:\n"
                + "\n".join(schema["name"].tolist())
            )

    st.divider()

    if "sql_result" in st.session_state:
        res = st.session_state["sql_result"]
        st.subheader("Results")
        st.dataframe(res, use_container_width=True, hide_index=True)

        col1, col2 = st.columns([1, 1])
        with col1:
            st.download_button(
                "📥 Download as CSV",
                res.to_csv(index=False).encode(),
                "query_result.csv",
                "text/csv",
                use_container_width=True,
            )
        with col2:
            st.download_button(
                "📥 Download as JSON",
                res.to_json().encode(),
                "query_result.json",
                "application/json",
                use_container_width=True,
            )
