"""Analysis layer."""
import pandas as pd
from database import get_connection


def run_query(sql, params=()):
    conn = get_connection()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
    finally:
        conn.close()
    return df


def get_filter_options():
    return {
        'years': run_query("SELECT DISTINCT substr(date,1,4) y FROM accidents ORDER BY y")['y'].tolist(),
        'severities': ['Fatal', 'Serious', 'Minor'],
        'states': run_query("SELECT DISTINCT state FROM locations ORDER BY state")['state'].tolist(),
    }


def get_kpis():
    conn = get_connection()
    cur = conn.cursor()
    total = cur.execute("SELECT COUNT(*) FROM accidents").fetchone()[0]
    fatal = cur.execute("SELECT COUNT(*) FROM accidents WHERE severity='Fatal'").fetchone()[0]
    deaths = cur.execute("SELECT COALESCE(SUM(num_fatalities),0) FROM accidents").fetchone()[0]
    states = cur.execute("SELECT COUNT(DISTINCT state) FROM locations").fetchone()[0]
    conn.close()
    return {'total': total, 'fatal': fatal, 'deaths': deaths, 'states': states}


def build_where(year, severities, state):
    where = ["substr(a.date,1,4) = ?", f"a.severity IN ({','.join(['?']*len(severities))})"]
    params = [year] + list(severities)
    if state != 'All':
        where.append("l.state = ?")
        params.append(state)
    return " AND ".join(where), params


def get_3d_data(year, severities, state):
    w, p = build_where(year, severities, state)
    return run_query(f"""
        SELECT a.date, a.severity, a.num_fatalities, a.num_injuries, a.light_condition,
               l.latitude, l.longitude, l.state, substr(a.date,1,7) AS month
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {w}
    """, tuple(p))


def get_heatmap_data(year, severities, state):
    w, p = build_where(year, severities, state)
    df = run_query(f"""
        SELECT a.time, a.date
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {w}
    """, tuple(p))
    if df.empty:
        return df
    df['hour'] = df['time'].str[:2].astype(int)
    df['dow'] = pd.to_datetime(df['date']).dt.day_name()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    pivot = df.groupby(['dow', 'hour']).size().unstack(fill_value=0)
    pivot = pivot.reindex([d for d in order if d in pivot.index])
    return pivot


def get_geo_data(year, severities, state):
    w, p = build_where(year, severities, state)
    return run_query(f"""
        SELECT l.latitude, l.longitude, a.severity, a.num_fatalities, l.state
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {w}
    """, tuple(p))


def get_severity_breakdown(year, severities, state):
    w, p = build_where(year, severities, state)
    return run_query(f"""
        SELECT a.severity, COUNT(*) AS count, SUM(a.num_fatalities) AS deaths
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        WHERE {w}
        GROUP BY a.severity
    """, tuple(p))
