import sqlite3
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

STATES = ['Maharashtra', 'Tamil Nadu', 'UP', 'Karnataka', 'Delhi', 'Gujarat', 'Rajasthan', 'Kerala']

conn = sqlite3.connect('accidents.db')
cur = conn.cursor()

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
    cur.execute("INSERT INTO weather_conditions(description,visibility_km) VALUES(?,?)",
        (w, round(random.uniform(0.5,15),1)))

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
print(f"✅ DONE: {len(df)} rows created")
conn.close()
