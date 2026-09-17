"""
generate_data.py
-----------------
Creates a synthetic but realistic Non-Financial Risk (NFR) incident dataset,
modeled on the Basel Committee's operational risk event-type taxonomy
(the same classification banks like RBI use internally).

The data is DELIBERATELY messy in places (inconsistent casing, stray
whitespace, a few bad dates, some missing financial-impact values, and a
handful of exact duplicate rows) so that etl.py has real cleaning work to do
-- that's the point of the "data preparation & transformation" project.

Run:
    python generate_data.py
Produces:
    data/raw_incidents.csv   (the "messy" source system export)
"""

import csv
import random
from datetime import datetime, timedelta

random.seed(42)

# --- Basel Level-1 / Level-2 operational risk taxonomy -------------------
TAXONOMY = {
    "Internal Fraud": ["Unauthorized Transactions", "Misappropriation of Assets", "Intentional Mis-reporting"],
    "External Fraud": ["Card Fraud", "Phishing / Social Engineering", "Cyber Theft"],
    "Employment Practices & Workplace Safety": ["Discrimination Claim", "Health & Safety Incident", "Employee Relations Dispute"],
    "Clients, Products & Business Practices": ["Mis-selling", "GDPR / Data Privacy Breach", "Suitability Breach"],
    "Damage to Physical Assets": ["Natural Disaster", "Vandalism", "Fire / Flood Damage"],
    "Business Disruption & System Failures": ["IT Outage", "Network Failure", "Third-Party Service Outage"],
    "Execution, Delivery & Process Management": ["Data Entry Error", "Failed Settlement", "Missed SLA", "Documentation Error"],
}

BUSINESS_UNITS = ["Retail Banking", "Corporate Banking", "Treasury", "Payments",
                  "IT Operations", "Compliance", "HR", "Risk Management"]

REGIONS = ["AT", "CZ", "SK", "HU", "RO", "HR", "RS", "BG"]  # RBI's core CEE footprint

SEVERITIES = ["Low", "Medium", "High", "Critical"]
SEVERITY_WEIGHTS = [0.45, 0.33, 0.17, 0.05]

STATUSES = ["Open", "In Progress", "Closed"]

ROLES = ["Branch Manager", "Risk Officer", "IT Support", "Compliance Officer",
         "Team Lead", "Customer Service Rep"]

N_ROWS = 900
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 9, 1)


def random_date(start, end):
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def messy_case(text: str) -> str:
    """Randomly mangle casing/whitespace to simulate a real source-system export."""
    r = random.random()
    if r < 0.15:
        return text.upper()
    if r < 0.30:
        return text.lower()
    if r < 0.40:
        return f"  {text}  "
    return text


def financial_impact_for(category: str, severity: str) -> float:
    base = {"Low": 500, "Medium": 5_000, "High": 50_000, "Critical": 400_000}[severity]
    # a bit of category flavor + lognormal-ish spread
    multiplier = random.lognormvariate(0, 0.6)
    if category in ("External Fraud", "Clients, Products & Business Practices"):
        multiplier *= 1.4
    return round(base * multiplier, 2)


def make_row(i: int) -> dict:
    category = random.choice(list(TAXONOMY.keys()))
    sub_category = random.choice(TAXONOMY[category])
    severity = random.choices(SEVERITIES, weights=SEVERITY_WEIGHTS)[0]
    occurred = random_date(START_DATE, END_DATE)
    reported_lag = random.randint(0, 12)
    reported = occurred + timedelta(days=reported_lag)
    status = random.choices(STATUSES, weights=[0.15, 0.20, 0.65])[0]
    resolution_days = None
    if status == "Closed":
        resolution_days = random.randint(1, 120)

    row = {
        "incident_id": f"NFR-{2024000 + i}",
        "date_occurred": occurred.strftime("%Y-%m-%d"),
        "date_reported": reported.strftime("%Y-%m-%d"),
        "business_unit": messy_case(random.choice(BUSINESS_UNITS)),
        "region": random.choice(REGIONS),
        "risk_category": messy_case(category),
        "sub_category": sub_category,
        "description": f"{sub_category} incident reported in {random.choice(BUSINESS_UNITS)} unit.",
        "severity": severity,
        "financial_impact_eur": financial_impact_for(category, severity),
        "status": status,
        "resolution_days": resolution_days,
        "reported_by_role": random.choice(ROLES),
        "control_failure": random.random() < 0.35,
    }

    # --- inject messiness -------------------------------------------------
    if random.random() < 0.06:
        row["financial_impact_eur"] = ""  # missing value
    if random.random() < 0.03:
        row["date_occurred"] = "31/02/2025"  # invalid date
    if random.random() < 0.02:
        row["date_reported"] = ""  # missing date

    return row


def main():
    rows = [make_row(i) for i in range(1, N_ROWS + 1)]

    # inject ~15 exact duplicate rows (as if the export ran twice)
    rows += random.sample(rows, 15)
    random.shuffle(rows)

    fieldnames = list(rows[0].keys())
    out_path = "data/raw_incidents.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {out_path}")


if __name__ == "__main__":
    main()
