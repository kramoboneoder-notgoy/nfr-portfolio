# Non-Financial Risk — Data & AI Automation Portfolio

Three small, connected projects around one theme: automating how a bank's
Non-Financial Risk function collects, cleans, analyses and reports
operational-risk incidents. All three share a synthetic incident dataset
modeled on the Basel operational-risk event-type taxonomy and a Central &
Eastern European region footprint.

| # | Project | What it covers | Tools |
| --- | --- | --- | --- |
| 1 | [Risk Incident ETL + Power BI Dashboard](01-risk-etl-powerbi/) | Cleaning a messy incident export, deriving risk KPIs, SQL analysis, an interactive risk dashboard | Python, pandas, SQLite, SQL, Power BI (DAX) |
| 2 | [Databricks Medallion Pipeline](02-databricks-pipeline/) | Bronze / Silver / Gold pipeline with Delta tables and a statistical outlier flag | PySpark, Delta Lake, Databricks Community Edition |
| 3 | [AI Risk Classifier & Summarizer](03-ai-risk-classifier/) | Turning free-text incident reports into structured risk data with an LLM | Python, LLM APIs (Anthropic / OpenAI), JSON |

![Project 1 dashboard](01-risk-etl-powerbi/dashboard.png)

## Quick start

```bash
git clone https://github.com/kramoboneoder-notgoy/nfr-portfolio.git
cd nfr-portfolio
pip install -r requirements.txt

# Project 1
cd 01-risk-etl-powerbi && python generate_data.py && python etl.py && cd ..

# Project 3 (mock mode, no API key needed)
cd 03-ai-risk-classifier && python risk_classifier.py --input sample_incidents.json && cd ..

# Project 2: import 02-databricks-pipeline/risk_medallion_pipeline.py into Databricks
```

Each folder has its own README with details, results and how to reproduce
them.

## Why one shared dataset

Using the same taxonomy and regions across all three projects is
deliberate: the repository is meant to read as one approach to
Non-Financial Risk automation — ingestion, pipeline, reporting, and an AI
layer on top — rather than three unrelated exercises.

## About the data

All incident data is synthetically generated (see `generate_data.py` in
Project 1 and the first cell of the Project 2 notebook). No real incidents,
customers or confidential information appear anywhere in this repository.

## Author

Bekarys — [github.com/kramoboneoder-notgoy](https://github.com/kramoboneoder-notgoy)
