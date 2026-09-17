# Project 1 — Non-Financial Risk Incident ETL Pipeline + Power BI Dashboard

Simulates a bank's Non-Financial Risk (NFR) incident register, cleans it with
pandas, loads it into SQLite, and turns it into a Power BI dashboard — the
exact chain named in the job posting: *"Assist in data preparation,
transformation, and analysis"* + *"Help build and maintain Power BI
dashboards and reports for risk purposes."*

## What's here

| File | Purpose |
| --- | --- |
| `generate_data.py` | Creates `data/raw_incidents.csv` — a messy, realistic export (bad dates, missing values, duplicates, inconsistent casing) using the Basel operational-risk event-type taxonomy |
| `etl.py` | Cleans the raw data, derives KPIs, writes `data/clean_incidents.csv` and `data/risk.db` (SQLite) |
| `analysis_queries.sql` | 5 example SQL queries against `risk.db` |
| `data/` | Output folder (raw + clean CSVs, SQLite DB) |

## Step 1 — Run the pipeline (5 minutes)

```bash
pip install pandas numpy
python generate_data.py   # -> data/raw_incidents.csv
python etl.py             # -> data/clean_incidents.csv, data/risk.db
```

You'll see console output showing how many bad rows were dropped/fixed —
screenshot this, it's good evidence of real data-cleaning work.

## Step 2 — Build the Power BI dashboard (60–90 minutes)

1. Open **Power BI Desktop** → **Get Data** → **Text/CSV** → select
   `data/clean_incidents.csv` → **Load**.
2. In the *Power Query Editor* (Transform Data), set correct types:
   `date_occurred`/`date_reported` → Date, `financial_impact_eur` → Decimal,
   `severity_score` → Whole Number. This step itself is worth mentioning in
   an interview — it shows you know Power BI's data model matters as much
   as the visuals.
3. Optionally also load `data/gold_monthly_summary` from `risk.db` (Get
   Data → ODBC, if you install a SQLite ODBC driver) as a second table, or
   just recompute the same aggregates with DAX (below) — either is fine to
   talk about, the CSV-only path is simplest under time pressure.
4. Create a **Date table** (Modeling → New Table):
   ```
   DateTable = CALENDAR(MIN(clean_incidents[date_occurred]), MAX(clean_incidents[date_occurred]))
   ```
   Mark it as a Date Table, then relate it to `clean_incidents[date_occurred]`.
5. Add these **DAX measures** (Modeling → New Measure):
   ```
   Total Incidents = COUNTROWS(clean_incidents)

   Total Financial Impact = SUM(clean_incidents[financial_impact_eur])

   Critical/High Incidents =
       CALCULATE([Total Incidents], clean_incidents[severity] IN {"High","Critical"})

   Control Failure Rate =
       DIVIDE(
           CALCULATE([Total Incidents], clean_incidents[control_failure] = TRUE),
           [Total Incidents]
       )

   Avg Resolution Days =
       AVERAGEX(FILTER(clean_incidents, clean_incidents[status] = "Closed"), clean_incidents[resolution_days])

   Incidents (Prior Month) =
       CALCULATE([Total Incidents], DATEADD(DateTable[Date], -1, MONTH))

   MoM Change % = DIVIDE([Total Incidents] - [Incidents (Prior Month)], [Incidents (Prior Month)])
   ```
6. Build the report page ("NFR Incident Overview"):
   - **KPI cards** across the top: Total Incidents, Total Financial Impact,
     Critical/High Incidents, Control Failure Rate.
   - **Line chart**: incidents per month (`month` on axis, `Total Incidents`
     as value) — shows the trend.
   - **Stacked bar chart**: incidents by `business_unit`, colored by
     `severity` — the "heatmap"-style view risk teams actually use.
   - **Matrix/table**: `risk_category` x `severity`, values = Total Incidents
     and Total Financial Impact — sortable, drillable.
   - **Slicers**: `region`, `status`, and a date range slicer on `month`.
7. Apply a clean theme (View → Themes) and title the page. Export a
   screenshot or short screen recording — this is what goes in your README
   and CV.

## Step 3 (optional, shows SQL) — run `analysis_queries.sql`

```bash
sqlite3 data/risk.db < analysis_queries.sql
```
or open `data/risk.db` in **DB Browser for SQLite** and run the queries
from the *Execute SQL* tab. Screenshot one result — it's a fast way to prove
SQL comfort without needing a live database server.

## Talking points for the interview

- "I modeled the incident data on Basel operational-risk event types, the
  same taxonomy banks use for regulatory NFR reporting."
- "The raw export was intentionally messy — I handled invalid dates,
  missing financial-impact values (imputed by category+severity median
  rather than dropped), and duplicate records."
- "I built the KPIs (control failure rate, aging buckets, MoM change) the
  way a risk team would actually want to monitor them, not just row counts."
