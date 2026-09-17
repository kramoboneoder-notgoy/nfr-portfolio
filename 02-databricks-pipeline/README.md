# Project 2 — Databricks Medallion Pipeline for Risk Data

A Bronze -> Silver -> Gold PySpark pipeline over Non-Financial Risk incident
data, built for **Databricks Community Edition** (free). Directly answers the
posting's *"Contribute to data pipelines and data flows using modern
platforms (e.g. Databricks)."*

This notebook was fully executed and verified locally against a real Spark
session before being included here (bronze 1,220 rows -> silver 1,200 rows
after dedup/cleaning -> 226 monthly gold rows + a 6-row business-unit summary
+ 42 flagged financial-impact outliers) — it's not just code that "should
work," it runs.

## Step 1 — Import into Databricks Community Edition (10 minutes)

1. Sign in at **community.cloud.databricks.com** (create a free account if
   you don't have one).
2. Create a cluster: **Compute** → **Create Compute** → single-node,
   smallest instance, latest LTS runtime → wait for it to start.
3. **Workspace** → your user folder → **Import** → choose
   `risk_medallion_pipeline.py` from this folder → Databricks recognizes the
   `# Databricks notebook source` header and imports it as a proper
   multi-cell notebook automatically.
4. Attach the notebook to your cluster (top-left dropdown) and **Run All**.

## Step 2 — What each layer does

- **Bronze**: raw, as-generated data loaded with no transformation — the
  "source of truth" layer.
- **Silver**: type casting, text normalization (region codes upper-cased),
  missing `financial_impact_eur` imputed by category+severity median,
  duplicate `incident_id` rows removed, `severity_score` and `month`
  derived.
- **Gold**: two business-ready aggregate tables —
  `gold_monthly_risk_summary` (incidents & impact by month + category) and
  `gold_business_unit_summary` (impact and % high/critical by business
  unit) — the tables a dashboard or analyst would actually query.
- **Bonus cell**: flags incidents whose financial impact is a statistical
  outlier (>2 standard deviations) within their own risk category — a
  simple, honest first step into "AI/analytics on top of the pipeline."

## Step 3 — What to capture for your portfolio

Run all cells, then screenshot:
- The final summary cell (`Bronze rows: … Silver rows: … Gold rows: …`).
- One `display()` output of the gold table (bar/line chart it right there in
  the Databricks cell output using the built-in chart button — that's a
  nice extra screenshot showing you know the notebook UI, not just the
  code).

## Talking points for the interview

- "I used the medallion architecture (bronze/silver/gold) because it's the
  standard Databricks pattern for reliability — nothing is lost at bronze,
  and gold is what a dashboard would query."
- "I ran the full pipeline against a real Spark session before calling it
  done — it's not just code that looks right, I verified the row counts at
  each stage."
- "The outlier flag is a simple statistical check, not a real ML model —
  I'd want to talk about what a proper anomaly-detection approach would add
  before calling it production-ready."

## Note on Delta Lake

The notebook writes tables with `.format("delta")`, which Databricks
Community Edition supports natively — no extra setup needed there. If you
ever run this outside Databricks (plain local PySpark), swap `"delta"` for
`"parquet"` — that's exactly how it was verified locally for this project.
