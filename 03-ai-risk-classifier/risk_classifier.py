#!/usr/bin/env python3
"""
risk_classifier.py
-------------------
An AI/LLM-powered tool that takes free-text Non-Financial Risk incident
descriptions (the kind an employee would type into an incident form) and:

  1. classifies each one into a Basel operational-risk event type + severity,
  2. extracts a structured JSON record (category, severity, estimated impact,
     recommended action, key entities mentioned),
  3. writes a short plain-English executive summary across a whole batch.

This directly targets the posting's "Leverage AI/LLM tools to improve
efficiency (e.g. automation, documentation, data analysis)" bullet — the
one line in the job description almost no other student applicant will have
a concrete project for.

MOCK MODE (default, no API key needed):
    Runs immediately using a small rule-based + cached-response fallback so
    you can demo it right now, with no signup and no cost.

LIVE MODE (optional, more impressive in an interview):
    Set ANTHROPIC_API_KEY (or OPENAI_API_KEY) in your environment and pass
    --live. The tool then calls the real API to do the classification.

Usage:
    python risk_classifier.py --input sample_incidents.json
    python risk_classifier.py --input sample_incidents.json --live
    python risk_classifier.py --text "A customer's account was debited twice due to a batch job bug."
"""

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, asdict
from typing import Optional

BASEL_CATEGORIES = [
    "Internal Fraud",
    "External Fraud",
    "Employment Practices & Workplace Safety",
    "Clients, Products & Business Practices",
    "Damage to Physical Assets",
    "Business Disruption & System Failures",
    "Execution, Delivery & Process Management",
]

SYSTEM_PROMPT = f"""You are a Non-Financial Risk analyst assistant at a bank.
Classify the given incident description into exactly one of these Basel
operational-risk event types: {", ".join(BASEL_CATEGORIES)}.

Respond with ONLY a JSON object with these exact keys:
{{
  "risk_category": one of the categories above,
  "severity": one of "Low", "Medium", "High", "Critical",
  "estimated_financial_impact_eur": a number (your best estimate, 0 if unclear),
  "recommended_action": one short sentence,
  "key_entities": a list of short strings (systems, roles, or amounts mentioned),
  "rationale": one short sentence explaining the classification
}}
No prose outside the JSON."""


@dataclass
class ClassificationResult:
    incident_text: str
    risk_category: str
    severity: str
    estimated_financial_impact_eur: float
    recommended_action: str
    key_entities: list
    rationale: str
    mode: str  # "mock" or "live"


# --------------------------------------------------------------------------
# MOCK MODE — deterministic keyword-based classifier, zero external calls.
# This is intentionally simple; its only job is to make the tool runnable
# out-of-the-box. LIVE MODE (below) is where an actual LLM does the work.
# --------------------------------------------------------------------------
_MOCK_RULES = [
    (r"\b(fraud|unauthorized|embezzl|misappropriat)\b.*\b(employee|staff|insider)\b", "Internal Fraud", "High"),
    (r"\b(access|accessed|viewed)\b.*\b(without\b.*\b(business reason|authorization|permission)|personal\s+\w+)\b",
     "Internal Fraud", "Medium"),
    (r"\b(phishing|card fraud|external|hack(ed|er)?|stolen card|skimm)\b", "External Fraud", "High"),
    (r"\b(discriminat|harassment|workplace injury|safety incident)\b", "Employment Practices & Workplace Safety", "Medium"),
    (r"\b(mis-?sold|mis-?selling|gdpr|data privacy|customer complaint|suitability)\b", "Clients, Products & Business Practices", "Medium"),
    (r"\b(fire|flood\w*|earthquake|vandal\w*|physical damage|branch damage|damaged the)\b", "Damage to Physical Assets", "High"),
    (r"\b(outage|system (down|unavailable)|network fail|server crash|it disruption|failover|core banking system)\b",
     "Business Disruption & System Failures", "High"),
    (r"\b(double.?debit|duplicate payment|data entry|manual error|re-?keyed|missed sla|settlement fail|batch job bug|processing error)\b",
     "Execution, Delivery & Process Management", "Medium"),
]

_SEVERITY_IMPACT = {"Low": 1_000, "Medium": 15_000, "High": 100_000, "Critical": 750_000}


def classify_mock(text: str) -> ClassificationResult:
    lowered = text.lower()
    category, severity = "Execution, Delivery & Process Management", "Low"  # default fallback
    for pattern, cat, sev in _MOCK_RULES:
        if re.search(pattern, lowered):
            category, severity = cat, sev
            break

    entities = re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", text)[:5]
    amounts = re.findall(r"(?:EUR|€)\s?[\d,.]+", text)
    key_entities = list(dict.fromkeys(entities + amounts))[:5]

    return ClassificationResult(
        incident_text=text,
        risk_category=category,
        severity=severity,
        estimated_financial_impact_eur=_SEVERITY_IMPACT[severity],
        recommended_action=f"Escalate to the {category.split(',')[0]} control owner for review within "
                            f"{'24 hours' if severity in ('High', 'Critical') else '5 business days'}.",
        key_entities=key_entities,
        rationale=f"Keyword match against a {category!r} pattern (mock mode — no LLM call made).",
        mode="mock",
    )


# --------------------------------------------------------------------------
# LIVE MODE — calls the Anthropic API (falls back to OpenAI if that key is
# set instead). Only imported/used when --live is passed, so mock mode has
# zero dependency on either SDK being installed.
# --------------------------------------------------------------------------
def classify_live(text: str) -> ClassificationResult:
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if anthropic_key:
        import anthropic
        client = anthropic.Anthropic(api_key=anthropic_key)
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=400,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text}],
        )
        raw = resp.content[0].text
    elif openai_key:
        from openai import OpenAI
        client = OpenAI(api_key=openai_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
        )
        raw = resp.choices[0].message.content
    else:
        raise RuntimeError(
            "No API key found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY, "
            "or drop --live to use mock mode."
        )

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(match.group(0) if match else raw)

    return ClassificationResult(
        incident_text=text,
        risk_category=data.get("risk_category", "Unknown"),
        severity=data.get("severity", "Unknown"),
        estimated_financial_impact_eur=float(data.get("estimated_financial_impact_eur", 0) or 0),
        recommended_action=data.get("recommended_action", ""),
        key_entities=data.get("key_entities", []),
        rationale=data.get("rationale", ""),
        mode="live",
    )


def classify(text: str, live: bool) -> ClassificationResult:
    if live:
        try:
            return classify_live(text)
        except Exception as exc:  # noqa: BLE001 -- surfaced to the user, not swallowed
            print(f"[warning] live classification failed ({exc}); falling back to mock mode", file=sys.stderr)
            return classify_mock(text)
    return classify_mock(text)


def summarize_batch(results: list) -> str:
    total = len(results)
    by_category = {}
    total_impact = 0.0
    high_severity = 0
    for r in results:
        by_category[r.risk_category] = by_category.get(r.risk_category, 0) + 1
        total_impact += r.estimated_financial_impact_eur
        if r.severity in ("High", "Critical"):
            high_severity += 1

    top_category = max(by_category, key=by_category.get) if by_category else "n/a"
    lines = [
        f"Processed {total} incident report(s).",
        f"Most common risk category: {top_category} ({by_category.get(top_category, 0)} incident(s)).",
        f"{high_severity} of {total} flagged High/Critical severity — recommend prioritized review.",
        f"Estimated total financial exposure across the batch: EUR {total_impact:,.0f}.",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Classify Non-Financial Risk incident text with an LLM.")
    parser.add_argument("--input", help="Path to a JSON file: a list of incident description strings.")
    parser.add_argument("--text", help="Classify a single incident description directly.")
    parser.add_argument("--live", action="store_true", help="Use a real LLM API call instead of mock mode.")
    parser.add_argument("--out", default="classified_incidents.json", help="Where to write the structured output.")
    args = parser.parse_args()

    if not args.input and not args.text:
        parser.error("Provide --input <file.json> or --text \"...\"")

    texts = [args.text] if args.text else json.load(open(args.input))

    results = [classify(t, live=args.live) for t in texts]

    with open(args.out, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)

    print(f"Mode: {'LIVE (LLM API)' if args.live else 'MOCK (rule-based, no API key needed)'}")
    print(f"Classified {len(results)} incident(s) -> {args.out}\n")
    for r in results:
        print(f"- [{r.severity:>8}] {r.risk_category}: {r.incident_text[:70]}...")

    print("\n=== Executive Summary ===")
    print(summarize_batch(results))


if __name__ == "__main__":
    main()
