"""ETL Pipeline — cleans raw CSV before loading into SQLite."""
import pandas as pd
import numpy as np
import sqlite3
import os


def clean_accidents_data(raw_csv_path, output_db_path):
    """
    Full ETL: Raw CSV → Clean DataFrame → SQLite.
    Handles: nulls, duplicates, types, outliers, date formatting.
    """
    print("=" * 60)
    print("ETL PIPELINE — ROAD ACCIDENT DATA")
    print("=" * 60)

    # ---------- STEP 1: EXTRACT ----------
    print("\n[1] EXTRACT — Loading raw CSV...")
    df = pd.read_csv(raw_csv_path)
    print(f"    Raw rows: {len(df)}")
    print(f"    Raw columns: {list(df.columns)}")

    # ---------- STEP 2: INITIAL QUALITY REPORT ----------
    print("\n[2] DATA QUALITY REPORT (BEFORE CLEANING)")
    print(f"    Null values per column:\n{df.isnull().sum().to_string()}")
    print(f"    Duplicate rows: {df.duplicated().sum()}")
    print(f"    Total records: {len(df)}")

    # ---------- STEP 3: TRANSFORM ----------
    print("\n[3] TRANSFORM — Applying cleaning rules...")

    # Rule 1: Drop rows with null critical fields
    critical = ['date', 'severity', 'latitude', 'longitude']
    before = len(df)
    df = df.dropna(subset=critical)
    print(f"    Rule 1 — Dropped nulls in critical cols: {before - len(df)} rows removed")

    # Rule 2: Remove exact duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"    Rule 2 — Removed duplicates: {before - len(df)} rows removed")

    # Rule 3: Type coercion — numeric fields
    for col in ['num_fatalities', 'num_injuries']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

    # Rule 4: Normalize date to ISO 8601
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df['date'] = df['date'].dt.strftime('%Y-%m-%d')

    # Rule 5: Standardize severity values
    if 'severity' in df.columns:
        df['severity'] = df['severity'].astype(str).str.strip().str.title()
        valid_sev = ['Fatal', 'Serious', 'Minor']
        before = len(df)
        df = df[df['severity'].isin(valid_sev)]
        print(f"    Rule 5 — Standardized severity: {before - len(df)} invalid rows dropped")

    # Rule 6: Outlier filtering — lat/lon must be within India's bounds
    before = len(df)
    df = df[
        (df['latitude'].between(8.0, 37.0)) &
        (df['longitude'].between(68.0, 98.0))
    ]
    print(f"    Rule 6 — Removed geographic outliers: {before - len(df)} rows removed")

    # Rule 7: Negative value guard
    for col in ['num_fatalities', 'num_injuries']:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    print(f"\n[4] FINAL CLEAN DATASET")
    print(f"    Rows after cleaning: {len(df)}")
    print(f"    Null values remaining: {df.isnull().sum().sum()}")

    # ---------- STEP 4: LOAD ----------
    print(f"\n[5] LOAD — Writing to SQLite: {output_db_path}")
    os.makedirs(os.path.dirname(output_db_path), exist_ok=True)
    conn = sqlite3.connect(output_db_path)
    df.to_sql('accidents_clean', conn, if_exists='replace', index=False)

    # Create index for fast queries
    conn.execute("CREATE INDEX IF NOT EXISTS idx_clean_date_sev ON accidents_clean(date, severity)")
    conn.commit()

    count = conn.execute("SELECT COUNT(*) FROM accidents_clean").fetchone()[0]
    conn.close()
    print(f"    ✅ Loaded {count} rows into accidents_clean table")
    print("=" * 60)

    return df


if __name__ == "__main__":
    clean_accidents_data(
        raw_csv_path="data/accidents.csv",
        output_db_path="database/accidents.db"
                                  )
