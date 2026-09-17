-- analysis_queries.sql
-- Example SQL you can run directly against data/risk.db (e.g. with the
-- `sqlite3` CLI, DB Browser for SQLite, or Power BI's SQLite ODBC connector)
-- to show SQL skills alongside the Python/Power BI work.
--
-- Try it:  sqlite3 data/risk.db < analysis_queries.sql

-- 1. Total financial impact and incident count by risk category
SELECT
    risk_category,
    COUNT(*)                       AS incident_count,
    ROUND(SUM(financial_impact_eur), 2)  AS total_impact_eur,
    ROUND(AVG(financial_impact_eur), 2)  AS avg_impact_eur
FROM fact_incidents
GROUP BY risk_category
ORDER BY total_impact_eur DESC;

-- 2. Monthly trend of Critical/High severity incidents
SELECT
    month,
    COUNT(*) AS high_severity_incidents
FROM fact_incidents
WHERE severity IN ('High', 'Critical')
GROUP BY month
ORDER BY month;

-- 3. Business unit x severity heatmap data (feeds a Power BI matrix visual)
SELECT
    business_unit,
    severity,
    COUNT(*) AS incident_count
FROM fact_incidents
GROUP BY business_unit, severity
ORDER BY business_unit, severity;

-- 4. Open/aging incidents that need attention (control failures, not yet closed)
SELECT
    incident_id, region, business_unit, risk_category, severity,
    status, age_days, control_failure
FROM fact_incidents
WHERE status != 'Closed' AND control_failure = 1
ORDER BY age_days DESC
LIMIT 25;

-- 5. Average resolution time (days) by risk category, closed incidents only
SELECT
    risk_category,
    ROUND(AVG(resolution_days), 1) AS avg_resolution_days,
    COUNT(*) AS closed_incidents
FROM fact_incidents
WHERE status = 'Closed'
GROUP BY risk_category
ORDER BY avg_resolution_days DESC;
