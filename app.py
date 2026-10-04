import os
import streamlit as st
import pandas as pd
import plotly.express as px
from database import get_connection, init_database

st.set_page_config(
    page_title="Road Accident Analytics",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.stApp { background: #081B2A; color: #e6eef5; }
[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0f2a40 0%, #102D40 100%);
    padding: 22px 18px; border-radius: 14px;
    border: 1px solid rgba(0,212,255,0.15);
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
[data-testid="stMetricLabel"] { color: #8899aa !important; font-size: 0.9em; }
[data-testid="stMetricValue"] { color: #00d4ff !important; font-size: 2em; font-weight: 700; }
h1, h2, h3, h4 { color: #ffffff !important; }
.stTabs [data-baseweb="tab-list"] { gap: 8px; }
.stTabs [data-baseweb="tab"] {
    background: #0f2a40; border-radius: 8px 8px 0 0; padding: 10px 18px;
    color: #8899aa; font-weight: 500;
}
.stTabs [aria-selected="true"] { background: #00d4ff !important; color: #081B2A !important; }
section[data-testid="stSidebar"] { background: #0a1a2a; border-right: 1px solid #102D40; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='background: linear-gradient(135deg, #0a2540 0%, #081B2A 100%);
            padding: 32px 28px; border-radius: 16px; margin-bottom: 24px;
            border-left: 4px solid #00d4ff;
            box-shadow: 0 8px 30px rgba(0,0,0,0.4);'>
    <h1 style='color: #ffffff; margin: 0; font-size: 2.3em; font-weight: 700;'>
        🚦 Road Accident Analytics
    </h1>
    <p style='color: #8899aa; margin: 10px 0 0 0; font-size: 1.1em;'>
        Interactive dashboard for accident patterns, hotspots, and temporal trends
    </p>
</div>
""", unsafe_allow_html=True)

status = init_database()

with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 8px 0 16px 0;'>
        <div style='font-size: 2.6em;'>🚦</div>
        <div style='color: #00d4ff; font-weight: 700; font-size: 1.15em; letter-spacing: 1px;'>
            ROAD SAFETY
        </div>
        <div style='color: #667788; font-size: 0.8em;'>Analytics Dashboard v2.0</div>
    </div>
    <hr style='border-color: #102D40; margin: 0 0 16px 0;'>
    <h3 style='color: #ffffff; font-size: 1em; margin-bottom: 12px;'>🔍 FILTERS</h3>
    """, unsafe_allow_html=True)

    conn = get_connection()
    years = pd.read_sql_query("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y DESC", conn)['y'].tolist()
    states = pd.read_sql_query("SELECT DISTINCT state FROM locations ORDER BY state", conn)['state'].tolist()
    conn.close()

    year = st.select_slider("Year", options=years, value=years[0] if years else 2024)
    severities = st.multiselect("Severity", ['Fatal', 'Serious', 'Minor'], default=['Fatal', 'Serious', 'Minor'])
    state = st.selectbox("State", ['All'] + states)

    st.markdown("<hr style='border-color: #102D40;'>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: #667788; font-size: 0.75em; line-height: 1.6;'>
        <strong style='color: #8899aa;'>DATABASE</strong><br>
        Shared temp path (cloud-safe)<br>
        <strong style='color: #8899aa;'>TABLES</strong><br>
        accidents · locations<br>
        weather_conditions · vehicles
    </div>
    """, unsafe_allow_html=True)

conn = get_connection()
total = pd.read_sql_query("SELECT COUNT(*) c FROM accidents", conn)['c'][0]
fatal = pd.read_sql_query("SELECT COUNT(*) c FROM accidents WHERE severity='Fatal'", conn)['c'][0]
deaths = pd.read_sql_query("SELECT COALESCE(SUM(num_fatalities),0) d FROM accidents", conn)['d'][0]
nloc = pd.read_sql_query("SELECT COUNT(DISTINCT state) c FROM locations", conn)['c'][0]
conn.close()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Accidents", f"{total:,}")
c2.metric("Fatal Crashes", f"{fatal:,}")
c3.metric("Total Deaths", f"{deaths:,}")
c4.metric("States Covered", nloc)

st.markdown("""
<div style='background: rgba(0,212,255,0.06); border-left: 3px solid #00d4ff;
            padding: 12px 18px; border-radius: 8px; margin: 16px 0 8px 0;
            color: #ccd6e0; font-size: 0.92em;'>
    💡 <strong>Status:</strong> {status}
</div>
""".format(status=status), unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "🌐 3D Animated", "📊 Time Heatmap", "🗺️ Geographic", "💻 SQL Runner"
])

with tab1:
    st.markdown("### 🌐 3D Animated Accident Distribution")
    st.caption("WebGL rendering · animation_frame = month")
    
    conn = get_connection()
    where = f"substr(a.date,1,4)='{year}' AND a.severity IN ({','.join(['?']*len(severities))})"
    params = list(severities)
    if state != 'All':
        where += " AND l.state=?"
        params.append(state)
    
    df = pd.read_sql_query(f"""
        SELECT a.date, a.severity, a.num_fatalities, a.num_injuries, a.light_condition,
               l.latitude, l.longitude, l.state, substr(a.date,1,7) AS month
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {where}
    """, conn, params=params)
    conn.close()
    
    if df.empty:
        st.warning("No data matches current filters.")
    else:
        df['size'] = df['num_injuries'] + 1
        fig = px.scatter_3d(
            df, x='longitude', y='latitude', z='num_fatalities',
            color='severity', size='size', animation_frame='month',
            color_discrete_map={'Fatal': '#ff2b2b', 'Serious': '#ffa500', 'Minor': '#2ecc71'},
            hover_data=['date', 'state', 'light_condition'],
            opacity=0.75, height=650
        )
        fig.update_layout(
            scene=dict(
                xaxis_title="Longitude", yaxis_title="Latitude",
                zaxis_title="Fatalities",
                bgcolor='rgb(10,15,25)',
                xaxis=dict(gridcolor='#102D40'), yaxis=dict(gridcolor='#102D40'),
                zaxis=dict(gridcolor='#102D40')
            ),
            paper_bgcolor='rgb(10,15,25)', font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.markdown("### 📊 Hour × Day-of-Week Density")
    st.caption("Accident frequency by hour and day")
    
    conn = get_connection()
    where = f"substr(a.date,1,4)='{year}' AND a.severity IN ({','.join(['?']*len(severities))})"
    params = list(severities)
    if state != 'All':
        where += " AND l.state=?"
        params.append(state)
    
    df = pd.read_sql_query(f"""
        SELECT a.time, a.date
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {where}
    """, conn, params=params)
    conn.close()
    
    if df.empty:
        st.warning("No data matches current filters.")
    else:
        df['hour'] = df['time'].str[:2].astype(int)
        df['dow'] = pd.to_datetime(df['date']).dt.day_name()
        order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        pivot = df.groupby(['dow', 'hour']).size().unstack(fill_value=0)
        pivot = pivot.reindex([d for d in order if d in pivot.index])
        
        fig = px.imshow(
            pivot, aspect='auto', color_continuous_scale='Inferno',
            labels=dict(x="Hour of Day", y="Day of Week", color="Accidents")
        )
        fig.update_layout(
            height=520, paper_bgcolor='rgb(10,15,25)', font_color='white',
            plot_bgcolor='rgb(10,15,25)'
        )
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.markdown("### 🗺️ Geographic Hotspot Distribution")
    st.caption("Latitude × Longitude scatter")
    
    conn = get_connection()
    where = f"substr(a.date,1,4)='{year}' AND a.severity IN ({','.join(['?']*len(severities))})"
    params = list(severities)
    if state != 'All':
        where += " AND l.state=?"
        params.append(state)
    
    df = pd.read_sql_query(f"""
        SELECT l.latitude, l.longitude, a.severity, a.num_fatalities, l.state
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {where}
    """, conn, params=params)
    conn.close()
    
    if df.empty:
        st.warning("No data matches current filters.")
    else:
        fig = px.scatter(
            df, x='longitude', y='latitude', color='severity',
            size='num_fatalities', size_max=22, hover_data=['state'],
            color_discrete_map={'Fatal': 'red', 'Serious': 'orange', 'Minor': 'green'},
            height=620
        )
        fig.update_layout(
            paper_bgcolor='rgb(10,15,25)', plot_bgcolor='rgb(10,15,25)',
            font_color='white',
            xaxis=dict(title="Longitude", gridcolor='#102D40'),
            yaxis=dict(title="Latitude", gridcolor='#102D40')
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.markdown("### 💻 Live SQL Query Runner")
    st.caption("Execute SQLite queries directly")
    
    sql = st.text_area(
        "Enter SQLite Query:",
        value="SELECT severity, COUNT(*) AS count, SUM(num_fatalities) AS deaths FROM accidents GROUP BY severity ORDER BY count DESC;",
        height=120
    )
    
    if st.button("▶ Execute Query", type="primary", use_container_width=True):
        try:
            conn = get_connection()
            res = pd.read_sql_query(sql, conn)
            conn.close()
            st.success(f"✅ Returned {len(res)} rows")
            st.dataframe(res, use_container_width=True)
            st.download_button(
                "⬇ Download CSV",
                res.to_csv(index=False).encode(),
                "query_result.csv", "text/csv"
            )
        except Exception as e:
            st.error(f"❌ SQLite Error: {str(e)}")

st.markdown("""
<div style='background: #0a1a2a; padding: 26px; border-radius: 14px;
            margin-top: 36px; border-top: 3px solid #00d4ff;'>
    <h4 style='color: #00d4ff; margin: 0 0 16px 0;'>⚙️ System Architecture</h4>
    <div style='display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px;'>
        <div style='background: rgba(0,212,255,0.05); padding: 14px; border-radius: 10px;
                    border-left: 3px solid #00d4ff;'>
            <strong style='color: #ffffff;'>📊 Data Layer</strong><br>
            <span style='color: #8899aa; font-size: 0.9em;'>SQLite (temp shared path)<br>
            4 tables · 5000 rows</span>
        </div>
        <div style='background: rgba(0,212,255,0.05); padding: 14px; border-radius: 10px;
                    border-left: 3px solid #00d4ff;'>
            <strong style='color: #ffffff;'>⚙️ Processing</strong><br>
            <span style='color: #8899aa; font-size: 0.9em;'>Pandas ETL<br>
            sqlite3 engine</span>
        </div>
        <div style='background: rgba(0,212,255,0.05); padding: 14px; border-radius: 10px;
                    border-left: 3px solid #00d4ff;'>
            <strong style='color: #ffffff;'>🎨 Presentation</strong><br>
            <span style='color: #8899aa; font-size: 0.9em;'>Streamlit + Plotly 3D<br>
            Reactive filtering</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)
