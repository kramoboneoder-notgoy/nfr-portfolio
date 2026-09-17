# Project 2 — Databricks Medallion Pipeline for Risk Data

A Bronze → Silver → Gold PySpark pipeline over Non-Financial Risk incident
data, written as a Databricks notebook and run on Databricks Community
Edition. It uses the same Basel operational-risk taxonomy and CEE region
footprint as Project 1, so the portfolio tells one story across tools.

<!-- After running on Databricks, add: ![Pipeline run](databricks_output.png) -->

## Layers

| Layer | Table | What it does |
| --- | --- | --- |
| Bronze | `bronze_nfr_incidents` | Raw incidents stored exactly as they landed — schema-on-read, nothing dropped, so any downstream issue can be traced to source |
| Silver | `silver_nfr_incidents` | Type casting, region codes normalized, missing `financial_impact_eur` imputed by category + severity median, duplicate `incident_id` rows removed, `severity_score` and `month` derived |
| Gold | `gold_monthly_risk_summary`, `gold_business_unit_summary` | Business-ready aggregates: incidents and impact by month × category, and per business unit with the share of High/Critical incidents |

A final cell flags incidents whose financial impact sits more than two
standard deviations from their category mean — a simple statistical outlier
check that sits on top of the pipeline rather than a claim to be a model.

All tables are written as Delta tables, which Databricks supports natively.

## Verified run

The notebook was executed end to end against a Spark session before
publishing: 1,220 bronze rows → 1,200 silver rows after deduplication and
cleaning → 226 monthly gold rows and a 6-row business-unit summary, with 42
incidents flagged as financial-impact outliers.

## Run it

1. Sign in to Databricks Community Edition and start a single-node cluster.
2. Workspace → Import → select `risk_medallion_pipeline.py`. The
   `# Databricks notebook source` header makes Databricks import it as a
   multi-cell notebook.
3. Attach the notebook to the cluster and Run All.

The notebook generates its own input data in the first cell, so no upload
or external storage is needed. Outside Databricks (plain local PySpark),
replace `"delta"` with `"parquet"` in the write calls.

## Files

| File | Purpose |
| --- | --- |
| `risk_medallion_pipeline.py` | The notebook: data generation, bronze/silver/gold, outlier flag, summary |
