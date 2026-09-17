# Project 3 — AI-Powered Risk Report Classifier & Summarizer

The single strongest differentiator in this portfolio: a Python tool that
uses an LLM to read free-text risk incident descriptions — the kind a
branch employee actually types into an incident form — and turns them into
structured, actionable data. This is a direct, concrete answer to the
posting's *"Leverage AI/LLM tools to improve efficiency (e.g. automation,
documentation, data analysis)"* — a line most other student applicants will
only be able to talk about in the abstract.

## What it does

For each incident description, it produces:
- a **Basel risk category** (Internal Fraud, External Fraud, Business
  Disruption, etc.) and a **severity** (Low/Medium/High/Critical),
- an **estimated financial impact**,
- a **recommended action** and the **key entities** mentioned,
- and, across a whole batch, a short **executive summary** (most common
  category, how many need urgent review, total exposure).

## Two modes — it runs right now, no setup

**Mock mode (default)** — a small rule-based classifier with zero external
dependencies or API keys. It exists purely so the tool is runnable and
demoable immediately:
```bash
python risk_classifier.py --input sample_incidents.json
```

**Live mode** — routes the same incidents through a real LLM call instead.
Set an API key and add `--live`:
```bash
export ANTHROPIC_API_KEY=sk-ant-...      # or OPENAI_API_KEY=sk-...
pip install anthropic                     # or: pip install openai
python risk_classifier.py --input sample_incidents.json --live
```
If the call fails for any reason (no key, network, quota), it prints a
warning and falls back to mock mode automatically rather than crashing —
worth mentioning as a small but deliberate reliability choice.

## Try a single incident

```bash
python risk_classifier.py --text "A hacker used a stolen card to make fraudulent purchases at an ATM."
```

## Verified output (mock mode, 7 sample incidents)

```
- [  Medium] Execution, Delivery & Process Management: A customer's account was debited twice...
- [  Medium] Internal Fraud: An employee accessed a colleague's customer file without...
- [    High] Business Disruption & System Failures: The core banking system was unavailable...
- [    High] External Fraud: A phishing email impersonating IT support...
- [  Medium] Clients, Products & Business Practices: A customer complained that a structured product...
- [    High] Damage to Physical Assets: Heavy flooding damaged the ground-floor branch office...
- [  Medium] Execution, Delivery & Process Management: A relationship manager manually re-keyed...

=== Executive Summary ===
Processed 7 incident report(s).
Most common risk category: Execution, Delivery & Process Management (2 incident(s)).
3 of 7 flagged High/Critical severity — recommend prioritized review.
Estimated total financial exposure across the batch: EUR 360,000.
```

## Where this could go next (good to mention proactively in an interview)

- A small Streamlit front-end so a risk officer could paste text and get
  results without the command line.
- Feed its structured JSON output straight into Project 1's `risk.db` /
  Power BI dashboard, so newly reported incidents flow automatically into
  the same reporting the rest of the portfolio builds.
- Add a lightweight eval set (a handful of hand-labeled incidents) to
  measure classification accuracy before trusting it on real reports.

## Talking points for the interview

- "I built two modes deliberately — mock mode means the tool is honest
  about what needs an API key versus what's just Python logic, and it means
  I can demo it without exposing or spending on a real key."
- "The output is structured JSON, not just a label — that's what makes it
  useful to *automate*, e.g. feeding a dashboard, rather than just a
  classification demo."
- "I'd want to validate this against real, hand-labeled incidents before
  trusting it in production — right now it's a working prototype, not a
  validated classifier."
