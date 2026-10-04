# 🚦 Road Accident Analysis Dashboard

A comprehensive data analysis and visualization dashboard for Indian road accident data built with **Streamlit**, **SQLite**, **Pandas**, and **Plotly**.

## 📊 Project Overview

This project analyzes road accident patterns across 8 Indian states with:
- **5,000+ accident records** from 2020-2025
- **200 unique locations** with coordinates
- **Interactive 3D visualizations** and heatmaps
- **Live SQL query runner** for custom analysis
- **Geographic hotspot mapping**

## 🏗️ Architecture

```
SQLite Database (accidents.db)
    ↓
Pandas Data Processing
    ↓
Streamlit Dashboard + Plotly Charts
```

## 📁 Files

- **`setup.py`** - Database and CSV generation script
- **`app.py`** - Main Streamlit dashboard application
- **`accidents.db`** - SQLite database with accident data
- **`accidents.csv`** - Exported accident data in CSV format
- **`requirements.txt`** - Python dependencies

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Generate Database
```bash
python setup.py
```
This creates:
- `accidents.db` with 5,000+ records
- `accidents.csv` with all accident data

### 3. Run Dashboard
```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

## 📊 Dashboard Features

### 🌐 3D Animated Visualization
- Interactive 3D scatter plot animated by month
- Color-coded by severity (Fatal/Serious/Minor)
- Size represents injuries
- WebGL rendering for performance

### 📈 Heatmap Analysis
- Hour × Day-of-Week density matrix
- Identify peak accident times
- Inferno color scale for intensity

### 🗺️ Geographic Map
- Scatter mapbox showing accident locations
- Colored by severity
- Bubble size = fatalities

### 💻 SQL Query Runner
- Execute custom SQLite queries
- Export results as CSV
- Built-in example queries

## 📊 Database Schema

### `accidents` Table
```
accident_id, date, time, severity, num_fatalities, 
num_injuries, location_id, weather_id, light_condition
```

### `locations` Table
```
location_id, state, latitude, longitude
```

### `weather_conditions` Table
```
weather_id, description, visibility_km
```

### `vehicles` Table
```
vehicle_id, accident_id, vehicle_type
```

## 🎯 Filter Options

- **Year**: Select from available years (2020-2025)
- **Severity**: Fatal, Serious, Minor
- **State**: All Indian states covered
- Real-time dashboard updates

## 📈 Key Statistics

- Total Accidents: 5,000+
- Fatal Crashes: ~15%
- States Covered: 8
- Time Period: 2020-2025

## 🛠️ Technologies Used

- **Streamlit** - Web framework
- **SQLite3** - Database
- **Pandas** - Data processing
- **Plotly** - Interactive visualizations
- **NumPy** - Numerical computations
- **Faker** - Data generation

## 📝 Notes

- Database seed is fixed (seed=42) for reproducible results
- All locations have realistic Indian coordinates
- Severity distribution: 15% Fatal, 35% Serious, 50% Minor
- Data spans 5-year period with varying daily patterns

## 🎓 Academic Project

**Mumbai University VAP (Visiting Associate Program)**

---

**Author**: 777-aoikingsley  
**Last Updated**: October 2026
