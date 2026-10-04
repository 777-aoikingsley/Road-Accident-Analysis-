import streamlit as st
import sqlite3, pandas as pd, os, random, numpy as np
import plotly.express as px
from datetime import datetime, timedelta

# --- AUTO-CREATE DB ON FIRST RUN (Streamlit Cloud has no setup.py execution) ---
def bootstrap_db():
    if os.path.exists('accidents.db'):
        return
    from faker import Faker
    fake = Faker('en_IN'); random.seed(42); np.random.seed(42)
    STATES = ['Maharashtra','Tamil Nadu','UP','Karnataka','Delhi','Gujarat','Rajasthan','Kerala']
    conn = sqlite3.connect('accidents.db'); cur = conn.cursor()
    cur.executescript("""
    CREATE TABLE locations(location_id INTEGER PRIMARY KEY AUTOINCREMENT,state TEXT,latitude REAL,longitude REAL);
    CREATE TABLE weather_conditions(weather_id INTEGER PRIMARY KEY AUTOINCREMENT,description TEXT,visibility_km REAL);
    CREATE TABLE accidents(accident_id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT,time TEXT,severity TEXT,num_fatalities INTEGER,num_injuries INTEGER,location_id INTEGER REFERENCES locations(location_id),weather_id INTEGER REFERENCES weather_conditions(weather_id),light_condition TEXT);
    CREATE TABLE vehicles(vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,accident_id INTEGER REFERENCES accidents(accident_id),vehicle_type TEXT);
    CREATE INDEX idx_acc_date_sev ON accidents(date,severity);
    """)
    for _ in range(200):
        cur.execute("INSERT INTO locations(state,latitude,longitude) VALUES(?,?,?)",
            (random.choice(STATES), round(random.uniform(8,35),4), round(random.uniform(68,97),4)))
    for w in ['Clear','Rainy','Foggy','Cloudy']:
        cur.execute("INSERT INTO weather_conditions(description,visibility_km) VALUES(?,?)",(w,round(random.uniform(0.5,15),1)))
    start = datetime(2020,1,1)
    for i in range(5000):
        d = start + timedelta(days=random.randint(0,1825), hours=random.randint(0,23))
        sev = random.choices(['Fatal','Serious','Minor'], weights=[0.15,0.35,0.50])[0]
        fat = random.randint(1,5) if sev=='Fatal' else random.randint(0,2)
        cur.execute("INSERT INTO accidents(date,time,severity,num_fatalities,num_injuries,location_id,weather_id,light_condition) VALUES(?,?,?,?,?,?,?,?)",
            (d.strftime('%Y-%m-%d'), d.strftime('%H:%M'), sev, fat, random.randint(0,10),
             random.randint(1,200), random.randint(1,4), random.choice(['Daylight','Dusk','Dark'])))
        cur.execute("INSERT INTO vehicles(accident_id,vehicle_type) VALUES(?,?)",
            (cur.lastrowid, random.choice(['Two-Wheeler','Car','Bus','Truck','Auto'])))
    conn.commit()
    df = pd.read_sql_query("SELECT a.*,l.state,l.latitude,l.longitude,w.description weather FROM accidents a JOIN locations l ON a.location_id=l.location_id JOIN weather_conditions w ON a.weather_id=w.weather_id", conn)
    df.to_csv('accidents.csv', index=False)
    conn.close()

bootstrap_db()

# --- APP ---
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

where = [f"substr(a.date,1,4)='{year}'", f"a.severity IN ({','.join(['?']*len(sev))})"]
params = list(sev)
if state != 'All':
    where.append("l.state = ?"); params.append(state)
w = " AND ".join(where)

tab1, tab2, tab3, tab4 = st.tabs(["🌐 3D Animated", "📊 Heatmap", "🗺️ Geo Map", "💻 SQL Runner"])

with tab1:
    st.subheader("3D Animated Accident Distribution")
    st.caption("Plotly WebGL · animation_frame='month'")
    df = q(f"""SELECT a.date,a.severity,a.num_fatalities,a.num_injuries,a.light_condition,
                      l.latitude,l.longitude,l.state,substr(a.date,1,7) as month
               FROM accidents a JOIN locations l ON a.location_id=l.location_id WHERE {w}""", tuple(params))
    df['size'] = df['num_injuries'] + 1
    fig = px.scatter_3d(df, x='longitude', y='latitude', z='num_fatalities',
        color='severity', size='size', animation_frame='month',
        color_discrete_map={'Fatal':'#ff2b2b','Serious':'#ffa500','Minor':'#2ecc71'},
        hover_data=['date','state','light_condition'], opacity=0.75, height=650)
    fig.update_layout(scene=dict(xaxis_title="Longitude", yaxis_title="Latitude",
        zaxis_title="Fatalities", bgcolor='rgb(10,15,25)'),
        paper_bgcolor='rgb(10,15,25)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Hour × Day-of-Week Density")
    df = q(f"""SELECT a.time,a.date FROM accidents a JOIN locations l
               ON a.location_id=l.location_id WHERE {w}""", tuple(params))
    df['hour'] = df['time'].str[:2].astype(int)
    df['dow'] = pd.to_datetime(df['date']).dt.day_name()
    pv = df.groupby(['dow','hour']).size().unstack(fill_value=0)
    order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    pv = pv.reindex([d for d in order if d in pv.index])
    fig = px.imshow(pv, aspect='auto', color_continuous_scale='Inferno',
        labels=dict(x="Hour", y="Day", color="Accidents"))
    fig.update_layout(height=500, paper_bgcolor='rgb(10,15,25)', font_color='white')
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.subheader("Geographic Hotspot Map")
    df = q(f"""SELECT l.latitude,l.longitude,a.severity,a.num_fatalities,l.state
               FROM accidents a JOIN locations l ON a.location_id=l.location_id WHERE {w}""", tuple(params))
    fig = px.scatter_mapbox(df, lat='latitude', lon='longitude', color='severity',
        size='num_fatalities', size_max=18,
        color_discrete_map={'Fatal':'red','Serious':'orange','Minor':'green'},
        zoom=4, height=600, mapbox_style="carto-darkmatter")
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader("💻 Live SQL Query Runner")
    st.caption("Executes on live SQLite database")
    sql = st.text_area("Enter SQLite Query:", height=150,
        value="SELECT severity, COUNT(*) as count, SUM(num_fatalities) as total_deaths\nFROM accidents\nGROUP BY severity\nORDER BY count DESC;")
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
