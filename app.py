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

# ---- Styling ---------------------------------------------------------------
st.markdown(
    """
    <style>
    :root {
        --bg: #0B0F19;
        --panel: #121A2A;
        --panel-soft: #1E293B;
        --panel-strong: #243244;
        --line: rgba(148, 163, 184, 0.22);
        --text: #F8FAFC;
        --muted: #CBD5E1;
        --accent: #6366F1;
        --accent-2: #8B5CF6;
        --success: #10B981;
        --warn: #F59E0B;
        --danger: #EF4444;
        --shadow: rgba(15, 23, 42, 0.45);
    }

    .stApp {
        background: var(--bg);
        color: var(--text);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #111827 100%);
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebarNav"] { background: transparent; }
    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
    }

    .topbar {
        background: linear-gradient(135deg, #111827 0%, #0B0F19 100%);
        border: 1px solid var(--line);
        border-radius: 20px;
        padding: 1.3rem 1.4rem;
        box-shadow: 0 18px 40px var(--shadow);
        margin-bottom: 1.2rem;
    }

    .brand {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: 0.02em;
        color: var(--text);
        margin: 0;
    }

    .subhead {
        font-size: 0.98rem;
        color: var(--muted);
        margin-top: 0.5rem;
    }

    .status-pill {
        display: inline-block;
        margin-top: 0.75rem;
        padding: 0.42rem 0.8rem;
        border-radius: 999px;
        background: rgba(99, 102, 241, 0.13);
        border: 1px solid rgba(99, 102, 241, 0.35);
        color: #C7D2FE;
        font-size: 0.8rem;
        font-weight: 600;
    }

    .metric-card, .panel, .sql-card {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.95), rgba(18, 26, 42, 0.96));
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.22);
        padding: 1rem 1rem;
        color: var(--text);
    }

    [data-testid="stMetric"] {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.95), rgba(18, 26, 42, 0.96));
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18);
        padding: 1rem 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: #CBD5E1 !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
    }

    [data-testid="stMetricValue"] {
        color: var(--text) !important;
        font-size: 2rem !important;
        font-weight: 800 !important;
    }

    .section-title {
        color: var(--text);
        font-size: 1.15rem;
        font-weight: 700;
        margin-bottom: 0.55rem;
    }

    .muted {
        color: var(--muted);
    }

    .chip {
        display: inline-block;
        padding: 0.34rem 0.7rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        border: 1px solid transparent;
    }

    .chip-fatal { background: rgba(239, 68, 68, 0.12); color: #FCA5A5; border-color: rgba(239,68,68,0.20); }
    .chip-serious { background: rgba(245, 158, 11, 0.12); color: #FCD34D; border-color: rgba(245,158,11,0.20); }
    .chip-minor { background: rgba(16, 185, 129, 0.12); color: #6EE7B7; border-color: rgba(16,185,129,0.20); }

    .sidebar-card {
        background: rgba(30, 41, 59, 0.65);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.85rem 0.9rem;
        color: var(--text);
        margin-bottom: 0.8rem;
    }

    .stButton > button {
        background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
        color: white;
        font-weight: 700;
        border: none;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        box-shadow: 0 8px 18px rgba(99, 102, 241, 0.2);
    }

    .stDownloadButton > button {
        background: rgba(30, 41, 59, 0.9);
        color: var(--text);
        border: 1px solid var(--line);
        border-radius: 10px;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.6rem;
        margin-bottom: 0.8rem;
    }

    .stTabs [data-baseweb="tab"] {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid var(--line);
        border-radius: 12px 12px 0 0;
        color: var(--muted);
        font-weight: 600;
        padding: 0.55rem 0.9rem;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.12));
        color: var(--text);
        border-color: rgba(99, 102, 241, 0.38);
    }

    .stDataFrame {
        border-radius: 14px;
        overflow: hidden;
        border: 1px solid var(--line);
    }

    textarea, input, select {
        background: #0F172A !important;
        color: var(--text) !important;
        border: 1px solid var(--line) !important;
        border-radius: 12px !important;
    }

    .element-container { margin-bottom: 0.3rem; }
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


def severity_badge(value: str):
    value = (value or "").strip()
    cls = {
        "Fatal": "chip-fatal",
        "Serious": "chip-serious",
        "Minor": "chip-minor",
    }.get(value, "chip-minor")
    return f'<span class="chip {cls}">{value}</span>'


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


# ---- Sidebar ---------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div style='text-align:center; padding: 12px 0 12px 0;'>
            <div style='font-size: 2.6rem;'>🚦</div>
            <div style='font-size: 1.2rem; font-weight: 800; letter-spacing: 0.08em; color: #F8FAFC;'>ROAD SAFETY</div>
            <div style='font-size: 0.78rem; color: #CBD5E1; margin-top: 0.3rem;'>Analytics Suite</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-card'>")
    nav = st.radio("Navigation", ["Overview", "Analytics", "SQL Workspace", "Settings"], index=0, label_visibility="collapsed")
    st.markdown("</div>")

    st.markdown("<div class='sidebar-card'>")
    years = run_sql("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y DESC")['y'].tolist()
    year = st.select_slider("Year", options=years, value=years[0] if years else 2024)
    st.markdown("</div>")

    st.markdown("<div class='sidebar-card'>")
    severity_opts = ["Fatal", "Serious", "Minor"]
    severities = st.multiselect("Severity", severity_opts, default=severity_opts)
    st.markdown("</div>")

    st.markdown("<div class='sidebar-card'>")
    states = run_sql("SELECT DISTINCT state FROM locations ORDER BY state")['state'].tolist()
    state = st.selectbox("State", ["All"] + states)
    st.markdown("</div>")

    st.markdown("<div class='sidebar-card'>")
    st.caption("Status")
    st.write(f"{status}")
    st.markdown("</div>")

# ---- Top bar ----------------------------------------------------------------
st.markdown(
    """
    <div class='topbar'>
        <div class='brand'>Road Accident Analytics</div>
        <div class='subhead'>Interactive insights for hotspots, severity distribution, time-based risk patterns, and custom SQL exploration.</div>
        <span class='status-pill'>Live • SQLite backend • cloud-safe init</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---- KPI cards -------------------------------------------------------------
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
    st.metric("Total Accidents", f"{int(metric_df['total'].iloc[0]):,}")
with k2:
    st.metric("Fatal Crashes", f"{int(metric_df['fatal'].iloc[0]):,}")
with k3:
    st.metric("Total Deaths", f"{int(metric_df['deaths'].iloc[0]):,}")
with k4:
    st.metric("States Covered", f"{int(metric_df['states'].iloc[0]):,}")

# ---- Main content -----------------------------------------------------------
if nav == "Overview":
    st.markdown("<div class='section-title'>Overview</div>", unsafe_allow_html=True)
    overview_col_a, overview_col_b = st.columns([1.3, 1])

    with overview_col_a:
        st.markdown("<div class='panel'>")
        st.markdown("<div class='section-title'>Severity distribution</div>", unsafe_allow_html=True)
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
        if sev_data.empty:
            st.info("No data for the selected filters.")
        else:
            fig = px.bar(
                sev_data,
                x="severity",
                y="count",
                color="severity",
                color_discrete_map={"Fatal": "#ef4444", "Serious": "#f59e0b", "Minor": "#10b981"},
                text="count",
                title="",
            )
            fig.update_layout(
                paper_bgcolor="#0F172A",
                plot_bgcolor="#0F172A",
                font_color="#F8FAFC",
                showlegend=False,
                margin=dict(l=20, r=20, t=10, b=10),
            )
            fig.update_xaxes(showgrid=False)
            fig.update_yaxes(showgrid=True, gridcolor="rgba(148,163,184,0.12)")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>")

    with overview_col_b:
        st.markdown("<div class='panel'>")
        st.markdown("<div class='section-title'>Severity chips</div>", unsafe_allow_html=True)
        if sev_data.empty:
            st.caption("No severity breakdown available.")
        else:
            for _, row in sev_data.iterrows():
                st.markdown(
                    f"<div style='margin-bottom: 0.65rem;'><span class='chip {"chip-fatal" if row['severity']=="Fatal" else "chip-serious" if row['severity']=="Serious" else "chip-minor"}'>{row['severity']}</span> &nbsp;<span style='color: #CBD5E1;'>Count: {row['count']} · Deaths: {row['deaths']}</span></div>",
                    unsafe_allow_html=True,
                )
        st.markdown("</div>")

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["3D Scatter", "Heatmap", "Geographic"])

    with tab1:
        st.markdown("<div class='panel'>")
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
            df['size'] = df['num_injuries'] + 1
            fig = px.scatter_3d(
                df,
                x='longitude',
                y='latitude',
                z='num_fatalities',
                color='severity',
                size='size',
                animation_frame='month',
                color_discrete_map={'Fatal': '#ef4444', 'Serious': '#f59e0b', 'Minor': '#10b981'},
                hover_data=['date', 'state', 'light_condition'],
                opacity=0.7,
                height=620,
            )
            fig.update_layout(
                scene=dict(
                    xaxis_title='Longitude',
                    yaxis_title='Latitude',
                    zaxis_title='Fatalities',
                    bgcolor='#0F172A',
                    xaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
                    yaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
                    zaxis=dict(gridcolor='rgba(148,163,184,0.12)'),
                ),
                paper_bgcolor='#0F172A',
                font_color='#F8FAFC',
                margin=dict(l=0, r=0, t=0, b=0),
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>")

    with tab2:
        st.markdown("<div class='panel'>")
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
            heat['hour'] = heat['time'].str[:2].astype(int)
            heat['dow'] = pd.to_datetime(heat['date']).dt.day_name()
            order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            pivot = heat.groupby(['dow', 'hour']).size().unstack(fill_value=0)
            pivot = pivot.reindex([d for d in order if d in pivot.index])
            fig = px.imshow(
                pivot,
                aspect='auto',
                color_continuous_scale='Inferno',
                labels=dict(x='Hour of Day', y='Day of Week', color='Accidents'),
                height=560,
            )
            fig.update_layout(
                paper_bgcolor='#0F172A',
                plot_bgcolor='#0F172A',
                font_color='#F8FAFC',
                margin=dict(l=20, r=20, t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>")

    with tab3:
        st.markdown("<div class='panel'>")
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
                x='longitude',
                y='latitude',
                color='severity',
                size='num_fatalities',
                size_max=22,
                hover_data=['state'],
                color_discrete_map={'Fatal': '#ef4444', 'Serious': '#f59e0b', 'Minor': '#10b981'},
                height=560,
            )
            fig.update_layout(
                paper_bgcolor='#0F172A',
                plot_bgcolor='#0F172A',
                font_color='#F8FAFC',
                xaxis=dict(title='Longitude', gridcolor='rgba(148,163,184,0.12)'),
                yaxis=dict(title='Latitude', gridcolor='rgba(148,163,184,0.12)'),
                legend_title_text='Severity',
                margin=dict(l=20, r=20, t=10, b=10),
            )
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>")

elif nav == "Analytics":
    st.markdown("<div class='section-title'>Analytics</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>")
    st.markdown("<div class='section-title'>Accident trends by month</div>", unsafe_allow_html=True)
    monthly = run_sql(
        f"""
        SELECT substr(date,1,7) AS month, COUNT(*) AS accidents
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {where}
        GROUP BY substr(date,1,7)
        ORDER BY month
        """,
        tuple(params),
    )
    if monthly.empty:
        st.info("No monthly trend data available.")
    else:
        fig = px.line(monthly, x='month', y='accidents', markers=True)
        fig.update_layout(
            paper_bgcolor='#0F172A',
            plot_bgcolor='#0F172A',
            font_color='#F8FAFC',
            xaxis_title='Month',
            yaxis_title='Accidents',
            margin=dict(l=20, r=20, t=10, b=10),
        )
        st.plotly_chart(fig, use_container_width=True)
    st.markdown("</div>")

elif nav == "SQL Workspace":
    st.markdown("<div class='section-title'>SQL Workspace</div>", unsafe_allow_html=True)
    left, right = st.columns([2, 1])

    with left:
        st.markdown("<div class='sql-card'>")
        sql = st.text_area(
            "Query",
            value="SELECT severity, COUNT(*) AS count, SUM(num_fatalities) AS deaths FROM accidents GROUP BY severity ORDER BY count DESC;",
            height=220,
        )
        if st.button("Run query", use_container_width=True):
            try:
                res = run_sql(sql)
                st.session_state['sql_result'] = res
                st.success(f"Returned {len(res)} rows")
            except Exception as e:
                st.error(f"SQLite error: {e}")
        st.markdown("</div>")

    with right:
        st.markdown("<div class='panel'>")
        st.markdown("<div class='section-title'>Schema</div>", unsafe_allow_html=True)
        schema = run_sql("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        if not schema.empty:
            for _, row in schema.iterrows():
                st.write(f"• {row['name']}")
        st.markdown("</div>")

    st.markdown("<br>", unsafe_allow_html=True)
    if 'sql_result' in st.session_state:
        res = st.session_state['sql_result']
        st.dataframe(res, use_container_width=True, hide_index=True)
        st.download_button(
            "Export CSV",
            res.to_csv(index=False).encode(),
            "query_result.csv",
            "text/csv",
            use_container_width=False,
        )

else:
    st.markdown("<div class='section-title'>Settings</div>", unsafe_allow_html=True)
    st.markdown("<div class='panel'>")
    st.write("Application settings and environment controls.")
    st.metric("DB path", os.path.join(os.path.dirname(os.path.abspath(__file__)), 'database'))
    st.metric("Status", status)
    st.markdown("</div>")

# ---- Footer -----------------------------------------------------------------
st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)
