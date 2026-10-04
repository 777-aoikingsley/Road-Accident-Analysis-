"""Database layer — self-initializing at import time."""
import os
import sqlite3
import random
import tempfile
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

DB_DIR = os.path.join(tempfile.gettempdir(), "road_vap")
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.path.join(DB_DIR, "accidents.db")
CSV_PATH = os.path.join(DB_DIR, "accidents.csv")

STATES = [
    "Maharashtra", "Tamil Nadu", "Uttar Pradesh", "Karnataka",
    "Delhi", "Gujarat", "Rajasthan", "Kerala"
]
WEATHER = ["Clear", "Rainy", "Foggy", "Cloudy"]
VEHICLES = ["Two-Wheeler", "Car", "Bus", "Truck", "Auto"]
LIGHT = ["Daylight", "Dusk", "Dark"]
SEVERITY = ["Fatal", "Serious", "Minor"]

SCHEMA = """
CREATE TABLE IF NOT EXISTS locations (
    location_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS weather_conditions (
    weather_id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    visibility_km REAL
);
CREATE TABLE IF NOT EXISTS accidents (
    accident_id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    time TEXT NOT NULL,
    severity TEXT,
    num_fatalities INTEGER DEFAULT 0,
    num_injuries INTEGER DEFAULT 0,
    location_id INTEGER REFERENCES locations(location_id),
    weather_id INTEGER REFERENCES weather_conditions(weather_id),
    light_condition TEXT
);
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    accident_id INTEGER REFERENCES accidents(accident_id),
    vehicle_type TEXT
);
CREATE INDEX IF NOT EXISTS idx_acc_date_sev ON accidents(date, severity);
"""


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def _seed(conn):
    """Insert 5000 synthetic rows."""
    random.seed(42)
    np.random.seed(42)
    cur = conn.cursor()

    for _ in range(200):
        cur.execute(
            "INSERT INTO locations(state, latitude, longitude) VALUES(?,?,?)",
            (
                random.choice(STATES),
                round(random.uniform(8, 35), 4),
                round(random.uniform(68, 97), 4),
            ),
        )

    for w in WEATHER:
        cur.execute(
            "INSERT INTO weather_conditions(description, visibility_km) VALUES(?,?)",
            (w, round(random.uniform(0.5, 15), 1)),
        )

    start = datetime(2020, 1, 1)
    for _ in range(5000):
        d = start + timedelta(days=random.randint(0, 1825), hours=random.randint(0, 23))
        sev = random.choices(SEVERITY, weights=[0.15, 0.35, 0.50])[0]
        fat = random.randint(1, 5) if sev == "Fatal" else random.randint(0, 2)
        cur.execute(
            """INSERT INTO accidents(date, time, severity, num_fatalities, num_injuries,
            location_id, weather_id, light_condition) VALUES(?,?,?,?,?,?,?,?)""",
            (
                d.strftime("%Y-%m-%d"),
                d.strftime("%H:%M"),
                sev,
                fat,
                random.randint(0, 10),
                random.randint(1, 200),
                random.randint(1, 4),
                random.choice(LIGHT),
            ),
        )
        cur.execute(
            "INSERT INTO vehicles(accident_id, vehicle_type) VALUES(?,?)",
            (cur.lastrowid, random.choice(VEHICLES)),
        )

    conn.commit()
    df = pd.read_sql_query(
        """
        SELECT a.accident_id, a.date, a.time, a.severity, a.num_fatalities,
               a.num_injuries, a.light_condition, l.state, l.latitude, l.longitude,
               w.description AS weather, w.visibility_km
        FROM accidents a
        JOIN locations l ON a.location_id = l.location_id
        JOIN weather_conditions w ON a.weather_id = w.weather_id
        """,
        conn,
    )
    os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
    df.to_csv(CSV_PATH, index=False)


def _ensure_db():
    """Called at import time. Creates tables + seeds if empty."""
    conn = get_connection()
    conn.executescript(SCHEMA)
    cur = conn.cursor()
    try:
        count = cur.execute("SELECT COUNT(*) FROM accidents").fetchone()[0]
    except sqlite3.OperationalError:
        count = 0
    if count == 0:
        _seed(conn)
    conn.close()


def init_database():
    """Public API used by app.py."""
    _ensure_db()
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM accidents").fetchone()[0]
    conn.close()
    return f"Ready: {count} rows"


def db_exists():
    return os.path.exists(DB_PATH)


# Critical: create DB at import time so no worker race condition.
_ensure_db()
