import streamlit as st
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="Road Accident Analytics", layout="wide", page_icon="🚦", initial_sidebar_state="expanded")

st.markdown("""
<style>
    * { margin: 0; padding: 0; }
    .stApp { background: linear-gradient(135deg, #0a0f1a 0%, #081B2A 100%); color: white; }
    [data-testid="stMetric"] { 
        background: linear-gradient(135deg, #102D40 0%, #0a1f2e 100%);
        padding: 20px; border-radius: 12px; border: 1px solid #00d4ff44;
        box-shadow: 0 8px 32px rgba(0, 212, 255, 0.1);
    }
    .metric-label { color: #8899aa; font-size: 0.9em; }
    .metric-value { color: #00d4ff; font-size: 2em; font-weight: bold; }
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 600; }
    .stTabs [data-baseweb="tab-list"] button { border-bottom: 2px solid transparent; }
    .stTabs [aria-selected="true"] { border-bottom-color: #00d4ff !important; }
    .stInfo { background: linear-gradient(135deg, #0d3d52 0%, #0a2540 100%); border-left: 4px solid #00d4ff; }
    .stSuccess { background: linear-gradient(135deg, #0d3d2e 0%, #0a2528 100%); border-left: 4px solid #00ff88; }
    .stError { background: linear-gradient(135deg, #3d0d0d 0%, #280a0a 100%); border-left: 4px solid #ff4444; }
</style>
""", unsafe_allow_html=True)

st.title("🚦 Road Accident Analytics Dashboard")

st.markdown("""
<div style='background: linear-gradient(135deg, #0d3d52 0%, #0a1f2e 100%); 
            padding: 30px; border-radius: 15px; margin-bottom: 25px; 
            border: 1px solid #00d4ff44; box-shadow: 0 8px 32px rgba(0, 212, 255, 0.08);'>
    <p style='color: #8899aa; margin: 0; font-size: 1.05em; line-height: 1.6;'>
        📊 <strong>Real-time accident pattern analysis</strong> with interactive 3D visualization, hotspot detection, and custom SQL queries.<br>
        <span style='color: #00d4ff; font-size: 0.9em;'>⚡ SQLite Backend • 5,000+ Records • Reactive Filtering • WebGL 3D</span>
    </p>
</div>
""", unsafe_allow_html=True)

# Database query function with error handling
@st.cache_data
def q(sql, params=()):
    try:
        conn = sqlite3.connect('accidents.db')
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return pd.DataFrame()

# Sidebar configuration
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 15px 0;'>
        <div style='font-size: 3em; margin-bottom: 8px;'>🚦</div>
        <div style='color: #00d4ff; font-weight: bold; font-size: 1.15em; letter-spacing: 2px;'>ROAD SAFETY</div>
        <div style='color: #8899aa; font-size: 0.85em; margin-top: 4px;'>Analytics Dashboard v3.0</div>
    </div>
    <hr style='border-color: #102D40; margin: 20px 0;'>
    """, unsafe_allow_html=True)
    
    st.subheader("🔍 Filters", divider="blue")
    
    try:
        years = q("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y DESC")['y'].tolist()
        year = st.select_slider("📅 Year", options=years, value=years[0] if years else 2024)
    except:
        year = 2024
        st.warning("Year filter unavailable")
    
    sev = st.multiselect("🚨 Severity", ['Fatal','Serious','Minor'], default=['Fatal','Serious','Minor'])
    
    try:
        states = q("SELECT DISTINCT state FROM locations ORDER BY state")['state'].tolist()
        state = st.selectbox("🌍 State", ['All'] + states)
    except:
        state = 'All'
        st.warning("State filter unavailable")
    
    st.divider()
    st.caption("**Database:** accidents.db")
    st.caption("**Tables:** accidents, locations, weather_conditions, vehicles")

# Fetch metrics
try:
    total = q("SELECT COUNT(*) c FROM accidents")['c'][0]
    fatal = q("SELECT COUNT(*) c FROM accidents WHERE severity='Fatal'")['c'][0]
    nloc = q("SELECT COUNT(DISTINCT state) c FROM locations")['c'][0]
except:
    total = fatal = nloc = 0
    st.error("Unable to load metrics")

# Display KPIs
col1, col2, col3 = st.columns(3, gap="medium")
with col1:
    st.metric("📊 Total Accidents", f"{total:,}", delta="incidents", delta_color="off")
with col2:
    st.metric("💀 Fatal Crashes", f"{fatal:,}", delta="high severity", delta_color="inverse")
with col3:
    st.metric("🗺️ States Covered", f"{nloc}", delta="regions", delta_color="off")

st.info("💡 **How to use:** Adjust filters in sidebar → Select tab below → Explore visualizations → Query custom data in SQL Runner")

st.divider()

# Build WHERE clause
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

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["🌐 3D Animated", "📊 Heatmap", "🗺️ Geo Map", "💻 SQL Runner"])

# TAB 1: 3D Scatter
with tab1:
    st.subheader("3D Animated Accident Distribution")
    st.caption("🎯 Plotly WebGL • Animated by month • Bubble size = injuries")
    
    try:
        df = q(f"""
            SELECT a.date, a.severity, a.num_fatalities, a.num_injuries, a.light_condition,
                   l.latitude, l.longitude, l.state, substr(a.date,1,7) as month
            FROM accidents a
            JOIN locations l ON a.location_id=l.location_id
            WHERE {where}
        """, tuple(params))
        
        if not df.empty:
            df['size'] = df['num_injuries'] + 1
            fig = px.scatter_3d(
                df,
                x='longitude',
                y='latitude',
                z='num_fatalities',
                color='severity',
                size='size',
                animation_frame='month',
                color_discrete_map={'Fatal':'#ff2b2b','Serious':'#ffa500','Minor':'#2ecc71'},
                hover_data=['date','state','light_condition'],
                opacity=0.75,
                height=700,
                title="Spatiotemporal Accident Patterns"
            )
            fig.update_layout(
                scene=dict(
                    xaxis_title="Longitude",
                    yaxis_title="Latitude",
                    zaxis_title="Fatalities",
                    bgcolor='rgb(10,15,25)',
                    gridcolor='rgb(40,60,80)'
                ),
                paper_bgcolor='rgb(10,15,25)',
                plot_bgcolor='rgb(10,15,25)',
                font_color='white',
                font=dict(size=11)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No data available for selected filters")
    except Exception as e:
        st.error(f"❌ Error loading 3D visualization: {str(e)}")

# TAB 2: Heatmap
with tab2:
    st.subheader("Hour × Day-of-Week Density Heatmap")
    st.caption("🔥 Shows accident concentration by time")
    
    try:
        df = q(f"""
            SELECT a.time, a.date
            FROM accidents a
            JOIN locations l ON a.location_id=l.location_id
            WHERE {where}
        """, tuple(params))
        
        if not df.empty:
            df['hour'] = df['time'].str[:2].astype(int)
            df['dow'] = pd.to_datetime(df['date']).dt.day_name()
            pv = df.groupby(['dow','hour']).size().unstack(fill_value=0)
            order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            pv = pv.reindex([d for d in order if d in pv.index])
            
            fig = px.imshow(
                pv,
                aspect='auto',
                color_continuous_scale='Inferno',
                labels=dict(x='Hour of Day', y='Day of Week', color='Incidents'),
                height=600,
                title="Accident Temporal Patterns"
            )
            fig.update_layout(
                paper_bgcolor='rgb(10,15,25)',
                plot_bgcolor='rgb(10,15,25)',
                font_color='white',
                font=dict(size=11)
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No data available for selected filters")
    except Exception as e:
        st.error(f"❌ Error loading heatmap: {str(e)}")

# TAB 3: Geographic Map
with tab3:
    st.subheader("Geographic Hotspot Map")
    st.caption("📍 Latitude × Longitude scatter • Color-coded by severity")
    
    try:
        df = q(f"""
            SELECT l.latitude, l.longitude, a.severity, a.num_fatalities, l.state
            FROM accidents a
            JOIN locations l ON a.location_id=l.location_id
            WHERE {where}
        """, tuple(params))
        
        if not df.empty:
            # Create scatter plot with proper x/y axes
            fig = px.scatter(
                df,
                x='longitude',
                y='latitude',
                color='severity',
                size='num_fatalities',
                hover_data=['state', 'num_fatalities'],
                size_max=25,
                color_discrete_map={'Fatal':'#ff2b2b','Serious':'#ffa500','Minor':'#2ecc71'},
                height=700,
                title="Geographic Accident Distribution"
            )
            
            fig.update_layout(
                paper_bgcolor='rgb(10,15,25)',
                plot_bgcolor='rgb(10,15,25)',
                font_color='white',
                font=dict(size=11),
                xaxis_title="Longitude",
                yaxis_title="Latitude",
                xaxis=dict(gridcolor='rgb(40,60,80)'),
                yaxis=dict(gridcolor='rgb(40,60,80)'),
                hovermode='closest'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("📭 No data available for selected filters")
    except Exception as e:
        st.error(f"❌ Error loading map: {str(e)}")

# TAB 4: SQL Runner
with tab4:
    st.subheader("💻 Live SQL Query Runner")
    st.caption("Execute custom SQLite queries against the accidents database")
    
    sql = st.text_area(
        "Enter SQLite Query:",
        height=150,
        value="SELECT severity, COUNT(*) as count, SUM(num_fatalities) as total_deaths\nFROM accidents\nGROUP BY severity\nORDER BY count DESC;",
        placeholder="SELECT * FROM accidents LIMIT 10;"
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        execute = st.button("▶ Execute Query", type="primary", use_container_width=True)
    
    if execute:
        try:
            res = q(sql)
            if not res.empty:
                st.success(f"✅ Query returned {len(res)} rows")
                st.dataframe(res, use_container_width=True, height=400)
                csv = res.to_csv(index=False)
                st.download_button("⬇ Download CSV", csv, "query_results.csv", "text/csv", use_container_width=True)
            else:
                st.info("Query executed but returned no rows")
        except Exception as e:
            st.error(f"SQLite Error: {str(e)}")

# Footer
st.markdown("""
<div style='background: linear-gradient(135deg, #0a1a2a 0%, #081b2a 100%); padding: 25px; border-radius: 12px; 
            margin-top: 40px; border-top: 2px solid #00d4ff; box-shadow: 0 8px 32px rgba(0, 212, 255, 0.08);'>
    <h4 style='color: #00d4ff; margin: 0 0 15px 0;'>⚙️ System Architecture — 3-Tier</h4>
    <div style='display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; color: #ccd6e0; margin-bottom: 20px;'>
        <div style='background: rgba(0,212,255,0.05); padding: 15px; border-radius: 8px; border-left: 3px solid #00d4ff;'>
            <strong style='color: white; display: block; margin-bottom: 5px;'>📊 Data Layer</strong>
            SQLite accidents.db<br>
            <span style='font-size: 0.9em; color: #8899aa;'>4 tables • WAL mode • B-tree indexes</span>
        </div>
        <div style='background: rgba(0,212,255,0.05); padding: 15px; border-radius: 8px; border-left: 3px solid #00d4ff;'>
            <strong style='color: white; display: block; margin-bottom: 5px;'>⚙️ Processing Layer</strong>
            Pandas ETL pipeline<br>
            <span style='font-size: 0.9em; color: #8899aa;'>sqlite3 query engine</span>
        </div>
        <div style='background: rgba(0,212,255,0.05); padding: 15px; border-radius: 8px; border-left: 3px solid #00d4ff;'>
            <strong style='color: white; display: block; margin-bottom: 5px;'>🎨 Presentation Layer</strong>
            Streamlit UI • Plotly WebGL<br>
            <span style='font-size: 0.9em; color: #8899aa;'>Reactive filtering</span>
        </div>
    </div>
    <hr style='border-color: #102D40; margin: 15px 0;'>
    <div style='color: #667788; font-size: 0.85em; text-align: center;'>
        🎓 <strong style='color: white;'>ROAD ACCIDENT ANALYSIS USING PYTHON</strong><br>
        <span style='color: #00d4ff; font-weight: 500;'>Python 3.x • SQLite • Pandas • Streamlit • Plotly 3D • WebGL</span>
    </div>
</div>
""", unsafe_allow_html=True)
