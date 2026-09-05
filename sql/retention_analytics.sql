-- Churn rate by latest auto-renewal status.
SELECT
    COALESCE(CAST(latest_is_auto_renew AS VARCHAR), 'no_history') AS latest_auto_renewal,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(is_churn), 2) AS churn_percent
FROM read_parquet('data/silver/customer_snapshot_2017-01-31.parquet')
GROUP BY 1
ORDER BY churn_percent DESC;

-- Churn rate by payment recency.
SELECT
    CASE
        WHEN days_since_last_transaction IS NULL THEN 'no safe payment history'
        WHEN days_since_last_transaction <= 7 THEN '0-7 days since payment'
        WHEN days_since_last_transaction <= 30 THEN '8-30 days since payment'
        WHEN days_since_last_transaction <= 90 THEN '31-90 days since payment'
        ELSE 'over 90 days since payment'
    END AS recency_segment,
    COUNT(*) AS customers,
    ROUND(100.0 * AVG(is_churn), 2) AS churn_percent
FROM read_parquet('data/silver/customer_snapshot_2017-01-31.parquet')
GROUP BY 1
ORDER BY churn_percent DESC;
