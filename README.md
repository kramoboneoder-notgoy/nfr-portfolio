# Non-Financial Risk — Data & AI Automation Portfolio

Built for an application to RBI's Non-Financial Risk Tribe (Student Job —
Data & AI Automation). Three small, connected projects that mirror the
actual bullet points in that posting, all built on one synthetic
Non-Financial Risk incident dataset modeled on the Basel operational-risk
event-type taxonomy.

| # | Project | Job requirement it targets | Tools |
| --- | --- | --- | --- |
| 1 | [Risk Incident ETL + Power BI Dashboard](01-risk-etl-powerbi/) | Data preparation/transformation & analysis; Power BI dashboards for risk purposes | Python, pandas, SQLite, SQL, Power BI |
| 2 | [Databricks Medallion Pipeline](02-databricks-pipeline/) | Data pipelines on modern platforms (e.g. Databricks) | PySpark, Delta Lake, Databricks Community Edition |
| 3 | [AI Risk Classifier & Summarizer](03-ai-risk-classifier/) | Leverage AI/LLM tools for automation, documentation, data analysis | Python, LLM APIs (Anthropic/OpenAI), JSON |

## Quick start

```bash
git clone <your-fork-of-this-repo>
cd nfr-portfolio
pip install -r requirements.txt

# Project 1
cd 01-risk-etl-powerbi && python generate_data.py && python etl.py && cd ..

# Project 3 (mock mode, no API key needed)
cd 03-ai-risk-classifier && python risk_classifier.py --input sample_incidents.json && cd ..

# Project 2 — import 02-databricks-pipeline/risk_medallion_pipeline.py
# into Databricks Community Edition (see that folder's README)
```

Each project folder has its own README with exact steps, screenshots to
take, and interview talking points.

## Why one shared dataset

All three projects use the same Basel event-type taxonomy and the same RBI
CEE region footprint (AT, CZ, SK, HU, RO, HR, RS, BG) rather than three
unrelated toy datasets. The intent is that this reads as one coherent
"how I'd approach Non-Financial Risk automation" case study, not three
disconnected coding exercises — the difference between "I did some Python
tutorials" and "I understand what this role actually does."

## About the data

All incident data is **synthetically generated** (see each project's
`generate_data.py`) — no real incidents, customers, or confidential
information are involved anywhere in this repository.

## Author

Built by Bekarys as part of a job application to RBI's Non-Financial Risk
Tribe (Student Job — Data & AI Automation, Vienna).
