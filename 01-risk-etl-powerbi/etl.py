"""
etl.py
------
Cleans and transforms the raw Non-Financial Risk incident export into an
analysis-ready dataset, and loads it into SQLite so the project also shows
basic SQL skills (a "plus" in the job posting).

Run:
    python etl.py
Reads:
    data/raw_incidents.csv
Writes:
    data/clean_incidents.csv   <- import THIS into Power BI (Get Data > Text/CSV)
    data/risk.db               <- SQLite database (fact_incidents + gold_monthly_summary)
"""

import sqlite3
import pandas as pd
import numpy as np

RAW_PATH = "data/raw_incidents.csv"
CLEAN_CSV_PATH = "data/clean_incidents.csv"
DB_PATH = "data/risk.db"

VALID_CATEGORIES = [
    "Internal Fraud",
    "External Fraud",
    "Employment Practices & Workplace Safety",
    "Clients, Products & Business Practices",
    "Damage to Physical Assets",
    "Business Disruption & System Failures",
    "Execution, Delivery & Process Management",
]

SEVERITY_ORDER = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str)
    print(f"Loaded {len(df)} raw rows")
    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # 1. Trim whitespace + normalize categorical casing on every text column
    text_cols = ["business_unit", "region", "risk_category", "sub_category",
                 "severity", "status", "reported_by_role"]
    for col in text_cols:
        df[col] = df[col].astype(str).str.strip()

    # normalize risk_category against the canonical taxonomy (case-insensitive match)
    lookup = {c.lower(): c for c in VALID_CATEGORIES}
    df["risk_category"] = df["risk_category"].str.lower().map(lookup).fillna(df["risk_category"])
    df["business_unit"] = df["business_unit"].str.title()

    # 2. Parse dates, coercing invalid values (e.g. "31/02/2025") to NaT
    df["date_occurred"] = pd.to_datetime(df["date_occurred"], errors="coerce")
    df["date_reported"] = pd.to_datetime(df["date_reported"], errors="coerce")
    before = len(df)
    df = df.dropna(subset=["date_occurred"])
    print(f"Dropped {before - len(df)} rows with an unparseable date_occurred")

    # fill a handful of missing date_reported with date_occurred (best-effort)
    df["date_reported"] = df["date_reported"].fillna(df["date_occurred"])

    # 3. Numeric cleanup
    df["financial_impact_eur"] = pd.to_numeric(df["financial_impact_eur"], errors="coerce")
    # impute missing financial impact with the median for that risk category + severity
    df["financial_impact_eur"] = df.groupby(["risk_category", "severity"])["financial_impact_eur"] \
        .transform(lambda s: s.fillna(s.median()))
    df["financial_impact_eur"] = df["financial_impact_eur"].round(2)

    df["resolution_days"] = pd.to_numeric(df["resolution_days"], errors="coerce")
    df["control_failure"] = df["control_failure"].astype(str).str.lower().isin(["true", "1"])

    # 4. Remove exact duplicate incidents (same id = same underlying event)
    before = len(df)
    df = df.drop_duplicates(subset=["incident_id"])
    print(f"Dropped {before - len(df)} duplicate incident rows")

    # 5. Derived / analytical fields
    df["severity_score"] = df["severity"].map(SEVERITY_ORDER)
    df["reporting_lag_days"] = (df["date_reported"] - df["date_occurred"]).dt.days
    df["month"] = df["date_occurred"].dt.to_period("M").astype(str)
    df["quarter"] = df["date_occurred"].dt.to_period("Q").astype(str)
    today = pd.Timestamp.today().normalize()
    df["age_days"] = np.where(
        df["status"] == "Closed",
        df["resolution_days"],
        (today - df["date_occurred"]).dt.days,
    )
    df["aging_bucket"] = pd.cut(
        df["age_days"].fillna(0),
        bins=[-1, 7, 30, 90, 10_000],
        labels=["0-7 days", "8-30 days", "31-90 days", "90+ days"],
    )

    df = df.sort_values("date_occurred").reset_index(drop=True)
    return df


def build_gold_summary(df: pd.DataFrame) -> pd.DataFrame:
    """A pre-aggregated table that's handy as a second Power BI source /
    for quick sanity-checking without opening Power BI at all."""
    gold = (
        df.groupby(["month", "risk_category"])
        .agg(
            incident_count=("incident_id", "count"),
            total_financial_impact_eur=("financial_impact_eur", "sum"),
            avg_severity_score=("severity_score", "mean"),
            control_failure_count=("control_failure", "sum"),
        )
        .reset_index()
        .sort_values(["month", "risk_category"])
    )
    return gold


def main():
    raw = load_raw(RAW_PATH)
    clean_df = clean(raw)
    gold = build_gold_summary(clean_df)

    clean_df.to_csv(CLEAN_CSV_PATH, index=False)
    print(f"Wrote {len(clean_df)} clean rows -> {CLEAN_CSV_PATH}")

    conn = sqlite3.connect(DB_PATH)
    clean_df.to_sql("fact_incidents", conn, if_exists="replace", index=False)
    gold.to_sql("gold_monthly_summary", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded fact_incidents + gold_monthly_summary -> {DB_PATH}")

    # quick console summary so you can sanity-check without opening anything
    print("\n--- Quick summary ---")
    print(clean_df["risk_category"].value_counts())
    print(f"\nTotal financial impact (EUR): {clean_df['financial_impact_eur'].sum():,.0f}")


if __name__ == "__main__":
    main()
