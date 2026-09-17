# Databricks notebook source
# MAGIC %md
# MAGIC # Non-Financial Risk Data Pipeline — Bronze / Silver / Gold (Databricks Community Edition)
# MAGIC
# MAGIC This notebook implements a small **medallion architecture** (Bronze -> Silver -> Gold)
# MAGIC over Non-Financial Risk incident data using PySpark, the pattern Databricks itself
# MAGIC recommends and the one you'll be expected to recognize on the job.
# MAGIC
# MAGIC It reuses the same synthetic incident data as Project 1 (Basel operational-risk
# MAGIC event types, RBI's CEE region footprint) so the whole portfolio tells one story,
# MAGIC but everything here runs standalone in Databricks Community Edition (free tier).
# MAGIC
# MAGIC **How to use this file:** Databricks can import a plain `.py` file with the
# MAGIC `# Databricks notebook source` header directly as a notebook
# MAGIC (Workspace -> Import -> file -> select this file). Each `# COMMAND ----------`
# MAGIC marker becomes its own cell.

# COMMAND ----------

# MAGIC %md ## 0. Setup — generate the raw data in-notebook (no external upload needed)
# MAGIC In a real job you'd point this at a landing zone (ADLS/S3/DBFS upload). Here we
# MAGIC generate the same messy synthetic export as Project 1 directly with Python so the
# MAGIC notebook is fully self-contained and runs with one click on Databricks CE.

# COMMAND ----------

import random
from datetime import datetime, timedelta

random.seed(42)

TAXONOMY = {
    "Internal Fraud": ["Unauthorized Transactions", "Misappropriation of Assets"],
    "External Fraud": ["Card Fraud", "Phishing / Social Engineering", "Cyber Theft"],
    "Employment Practices & Workplace Safety": ["Discrimination Claim", "Health & Safety Incident"],
    "Clients, Products & Business Practices": ["Mis-selling", "GDPR / Data Privacy Breach"],
    "Damage to Physical Assets": ["Natural Disaster", "Vandalism"],
    "Business Disruption & System Failures": ["IT Outage", "Network Failure", "Third-Party Service Outage"],
    "Execution, Delivery & Process Management": ["Data Entry Error", "Failed Settlement", "Missed SLA"],
}
BUSINESS_UNITS = ["Retail Banking", "Corporate Banking", "Treasury", "Payments", "IT Operations", "Compliance"]
REGIONS = ["AT", "CZ", "SK", "HU", "RO", "HR", "RS", "BG"]
SEVERITIES = ["Low", "Medium", "High", "Critical"]
START, END = datetime(2024, 1, 1), datetime(2026, 9, 1)


def random_date():
    return (START + timedelta(days=random.randint(0, (END - START).days))).strftime("%Y-%m-%d")


def make_row(i):
    cat = random.choice(list(TAXONOMY.keys()))
    sev = random.choices(SEVERITIES, weights=[0.45, 0.33, 0.17, 0.05])[0]
    impact = {"Low": 500, "Medium": 5000, "High": 50000, "Critical": 400000}[sev] * random.lognormvariate(0, 0.6)
    row = {
        "incident_id": f"NFR-{2024000+i}",
        "date_occurred": random_date(),
        "business_unit": random.choice(BUSINESS_UNITS),
        "region": random.choice(REGIONS),
        "risk_category": cat,
        "sub_category": random.choice(TAXONOMY[cat]),
        "severity": sev,
        "financial_impact_eur": round(impact, 2),
        "status": random.choices(["Open", "In Progress", "Closed"], weights=[0.15, 0.2, 0.65])[0],
    }
    # inject a little messiness for the bronze/silver split to matter
    if random.random() < 0.05:
        row["financial_impact_eur"] = None
    if random.random() < 0.02:
        row["region"] = row["region"].lower()
    return row


raw_rows = [make_row(i) for i in range(1, 1201)]
raw_rows += random.sample(raw_rows, 20)  # duplicate a few rows on purpose
print(f"Generated {len(raw_rows)} raw rows")

# COMMAND ----------

# MAGIC %md ## 1. Bronze layer — raw ingestion, as-is
# MAGIC Bronze keeps the data exactly as it landed (schema-on-read, no cleaning), so
# MAGIC nothing is ever lost and any downstream bug can be traced back to source.

# COMMAND ----------

from pyspark.sql import Row

bronze_df = spark.createDataFrame([Row(**r) for r in raw_rows])
bronze_df.write.mode("overwrite").format("delta").saveAsTable("bronze_nfr_incidents")

print(f"Bronze row count: {bronze_df.count()}")
display(bronze_df.limit(10))

# COMMAND ----------

# MAGIC %md ## 2. Silver layer — cleaned, validated, deduplicated
# MAGIC Standard silver-layer responsibilities: type casting, null handling,
# MAGIC normalization, dedup on business key.

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.window import Window

bronze = spark.table("bronze_nfr_incidents")

silver_df = (
    bronze
    .withColumn("region", F.upper(F.trim(F.col("region"))))
    .withColumn("date_occurred", F.to_date("date_occurred", "yyyy-MM-dd"))
    .withColumn("financial_impact_eur", F.col("financial_impact_eur").cast("double"))
)

# impute missing financial impact with the category+severity median
med = (
    silver_df.groupBy("risk_category", "severity")
    .agg(F.expr("percentile_approx(financial_impact_eur, 0.5)").alias("median_impact"))
)
silver_df = (
    silver_df.join(med, on=["risk_category", "severity"], how="left")
    .withColumn(
        "financial_impact_eur",
        F.when(F.col("financial_impact_eur").isNull(), F.col("median_impact")).otherwise(F.col("financial_impact_eur")),
    )
    .drop("median_impact")
)

# dedupe on incident_id (keep first occurrence)
w = Window.partitionBy("incident_id").orderBy(F.lit(1))
silver_df = (
    silver_df.withColumn("_rn", F.row_number().over(w))
    .filter(F.col("_rn") == 1)
    .drop("_rn")
)

silver_df = silver_df.withColumn(
    "severity_score",
    F.when(F.col("severity") == "Low", 1)
     .when(F.col("severity") == "Medium", 2)
     .when(F.col("severity") == "High", 3)
     .otherwise(4),
).withColumn("month", F.date_format("date_occurred", "yyyy-MM"))

silver_df.write.mode("overwrite").format("delta").saveAsTable("silver_nfr_incidents")

print(f"Bronze -> Silver: {bronze.count()} -> {silver_df.count()} rows (dupes + bad rows removed)")
display(silver_df.limit(10))

# COMMAND ----------

# MAGIC %md ## 3. Gold layer — business-ready aggregates
# MAGIC Gold tables are what Power BI / a dashboard / an analyst actually queries —
# MAGIC pre-aggregated, fast, and shaped around a specific question.

# COMMAND ----------

silver = spark.table("silver_nfr_incidents")

gold_monthly = (
    silver.groupBy("month", "risk_category")
    .agg(
        F.count("*").alias("incident_count"),
        F.round(F.sum("financial_impact_eur"), 2).alias("total_impact_eur"),
        F.round(F.avg("severity_score"), 2).alias("avg_severity_score"),
    )
    .orderBy("month", "risk_category")
)
gold_monthly.write.mode("overwrite").format("delta").saveAsTable("gold_monthly_risk_summary")

gold_business_unit = (
    silver.groupBy("business_unit")
    .agg(
        F.count("*").alias("incident_count"),
        F.round(F.sum("financial_impact_eur"), 2).alias("total_impact_eur"),
        F.round(F.avg(F.when(F.col("severity").isin("High", "Critical"), 1).otherwise(0)) * 100, 1).alias("pct_high_or_critical"),
    )
    .orderBy(F.desc("total_impact_eur"))
)
gold_business_unit.write.mode("overwrite").format("delta").saveAsTable("gold_business_unit_summary")

display(gold_monthly)
display(gold_business_unit)

# COMMAND ----------

# MAGIC %md ## 4. A simple anomaly flag (stretch goal, worth showing off)
# MAGIC Flags incidents whose financial impact is a statistical outlier within their
# MAGIC own risk category — a first, honest step toward "AI/analytics on top of the
# MAGIC pipeline" without pretending it's a full ML model.

# COMMAND ----------

stats = silver.groupBy("risk_category").agg(
    F.avg("financial_impact_eur").alias("cat_mean"),
    F.stddev("financial_impact_eur").alias("cat_std"),
)

flagged = (
    silver.join(stats, on="risk_category", how="left")
    .withColumn(
        "is_outlier_impact",
        F.abs(F.col("financial_impact_eur") - F.col("cat_mean")) > 2 * F.col("cat_std"),
    )
)

flagged.filter(F.col("is_outlier_impact")).select(
    "incident_id", "risk_category", "severity", "financial_impact_eur", "cat_mean"
).orderBy(F.desc("financial_impact_eur")).show(15, truncate=False)

# COMMAND ----------

# MAGIC %md ## 5. Sanity-check summary
# MAGIC Run this last cell and screenshot the output — it's your proof the whole
# MAGIC bronze -> silver -> gold pipeline ran end to end on Databricks.

# COMMAND ----------

print("Bronze rows:", spark.table("bronze_nfr_incidents").count())
print("Silver rows:", spark.table("silver_nfr_incidents").count())
print("Gold (monthly) rows:", spark.table("gold_monthly_risk_summary").count())
print("Gold (business unit) rows:", spark.table("gold_business_unit_summary").count())
print("Flagged outlier incidents:", flagged.filter(F.col("is_outlier_impact")).count())
