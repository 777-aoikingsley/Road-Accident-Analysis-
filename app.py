import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Road Accident Analysis", layout="wide", page_icon="🚦")

st.markdown("""
<style>
.stApp { background-color: #081B2A; color: white; }
[data-testid="stMetric"] { background-color: #102D40; padding: 20px; border-radius: 15px; border: 1px solid #00d4ff33; }
h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

st.title("🚦 Road Accident Data Analysis")
st.caption("SQLite · Pandas · Streamlit · Plotly 3D | Mumbai University VAP")

@st.cache_data
def q(sql, params=()):
    conn = sqlite3.connect('accidents.db')
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

with st.sidebar:
    st.header("🔍 Filters")
    years = q("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y")['y'].tolist()
    year = st.select_slider("Year", options=years, value=years[-1])
    sev = st.multiselect("Severity", ['Fatal','Serious','Minor'], default=['Fatal','Serious','Minor'])
    states = q("SELECT DISTINCT state FROM locations ORDER BY state")['state'].tolist()
    state = st.selectbox("State", ['All'] + states)
    st.divider()
    st.caption("**Backend:** accidents.db")
    st.caption("**Tables:** accidents · locations · weather_conditions · vehicles")

total = q("SELECT COUNT(*) c FROM accidents")['c'][0]
fatal = q("SELECT COUNT(*) c FROM accidents WHERE severity='Fatal'")['c'][0]
nloc = q("SELECT COUNT(DISTINCT state) c FROM locations")['c'][0]

c1, c2, c3 = st.columns(3)
c1.metric("Total Accidents", f"{total:,}")
c2.metric("Fatal Crashes", f"{fatal:,}")
c3.metric("States Covered", nloc)

st.divider()

where_clauses = [f"substr(a.date,1,4)='{year}'"]
params = []
if sev:
    placeholders = ','.join(['?'] * len(sev))
    where_clauses.append(f"a.severity IN ({placeholders})")
    params.extend(sev)
if state != 'All':
    where_clauses.append("l.state = ?")
    params.append(state)
where = " AND ".join(where_clauses)

tab1, tab2, tab3, tab4 = st.tabs(["🌐 3D Animated", "📊 Heatmap", "🗺️ Geo Map", "💻 SQL Runner"])

with tab1:
    st.subheader("3D Animated Accident Distribution")
    st.caption("Plotly WebGL · animation_frame='month'")
    df = q(f"""
        SELECT a.date,a.severity,a.num_fatalities,a.num_injuries,a.light_condition,
               l.latitude,l.longitude,l.state,substr(a.date,1,7) as month
        FROM accidents a JOIN locations l ON a.location_id=l.location_id
        WHERE {where}
    """, tuple(params))
    if not df.empty:
        df['size'] = df['num_injuries'] + 1
        fig = px.scatter_3d(
            df,
            x='longitude', y='latitude', z='num_fatalities',
            color='severity', size='size', animation_frame='month',
            color_discrete_map={'Fatal':'#ff2b2b','Serious':'#ffa500','Minor':'#2ecc71'},
            hover_data=['date','state','light_condition'], opacity=0.75, height=650
        )
        fig.update_layout(
            scene=dict(xaxis_title="Longitude", yaxis_title="Latitude", zaxis_title="Fatalities", bgcolor='rgb(10,15,25)'),
            paper_bgcolor='rgb(10,15,25)', font_color='white'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters")

with tab2:
    st.subheader("Hour × Day-of-Week Density")
    df = q(f"""
        SELECT a.time,a.date FROM accidents a JOIN locations l
        ON a.location_id=l.location_id WHERE {where}
    """, tuple(params))
    if not df.empty:
        df['hour'] = df['time'].str[:2].astype(int)
        df['dow'] = pd.to_datetime(df['date']).dt.day_name()
        pv = df.groupby(['dow','hour']).size().unstack(fill_value=0)
        order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        pv = pv.reindex([d for d in order if d in pv.index])
        fig = px.imshow(pv, aspect='auto', color_continuous_scale='Inferno', labels=dict(x='Hour', y='Day', color='Accidents'))
        fig.update_layout(height=500, paper_bgcolor='rgb(10,15,25)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters")

with tab3:
    st.subheader("Geographic Hotspot Map")
    st.caption("Latitude × Longitude scatter — severity color-coded")
    df = q(f"""SELECT l.latitude,l.longitude,a.severity,a.num_fatalities,l.state
               FROM accidents a JOIN locations l ON a.location_id=l.location_id WHERE {where}""", tuple(params))
    fig = px.scatter(df, x='longitude', y='latitude', color='severity',
        size='num_fatalities', size_max=25, hover_data=['state'],
        color_discrete_map={'Fatal':'red','Serious':'orange','Minor':'green'},
        height=600)
    fig.update_layout(paper_bgcolor='rgb(10,15,25)', plot_bgcolor='rgb(10,15,25)',
        font_color='white', xaxis_title="Longitude", yaxis_title="Latitude")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("💻 Live SQL Query Runner")
    st.caption("Executes on live SQLite database")
    sql = st.text_area("Enter SQLite Query:", height=150, value="SELECT severity, COUNT(*) as count, SUM(num_fatalities) as total_deaths\nFROM accidents\nGROUP BY severity\nORDER BY count DESC;")
    if st.button("▶ Execute Query", type="primary"):
        try:
            res = q(sql)
            st.success(f"✅ Returned {len(res)} rows")
            st.dataframe(res, use_container_width=True)
            st.download_button("⬇ Download CSV", res.to_csv(index=False).encode(), "result.csv", "text/csv")
        except Exception as e:
            st.error(f"SQLite Error: {e}")

st.divider()
st.caption("**Architecture:** 3-tier — SQLite (Data) → Pandas + sqlite3 (Processing) → Streamlit + Plotly (Presentation)")
