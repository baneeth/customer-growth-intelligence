from pathlib import Path
import sys
import csv

import duckdb


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
SNAPSHOT = PROJECT_ROOT / "data" / "silver" / "customer_snapshot_2017-01-31.parquet"
REPORTS = PROJECT_ROOT / "reports"
TABLES = REPORTS / "tables"


QUERIES = {
    "churn_by_latest_auto_renewal": """
        SELECT
            COALESCE(CAST(latest_is_auto_renew AS VARCHAR), 'no_history') AS latest_auto_renewal,
            COUNT(*) AS customers,
            ROUND(100.0 * AVG(is_churn), 2) AS churn_percent
        FROM snapshot
        GROUP BY 1
        ORDER BY churn_percent DESC
    """,
    "churn_by_payment_recency": """
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
        FROM snapshot
        GROUP BY 1
        ORDER BY churn_percent DESC
    """,
    "churn_by_transaction_frequency": """
        SELECT
            CASE
                WHEN transaction_count_to_cutoff = 0 THEN 'no safe payment history'
                WHEN transaction_count_to_cutoff <= 3 THEN '1-3 payments'
                WHEN transaction_count_to_cutoff <= 10 THEN '4-10 payments'
                WHEN transaction_count_to_cutoff <= 25 THEN '11-25 payments'
                ELSE '26+ payments'
            END AS payment_frequency_segment,
            COUNT(*) AS customers,
            ROUND(100.0 * AVG(is_churn), 2) AS churn_percent
        FROM snapshot
        GROUP BY 1
        ORDER BY churn_percent DESC
    """,
    "churn_by_profile_availability": """
        SELECT
            has_transaction_history_flag,
            has_member_profile_flag,
            COUNT(*) AS customers,
            ROUND(100.0 * AVG(is_churn), 2) AS churn_percent
        FROM snapshot
        GROUP BY 1, 2
        ORDER BY churn_percent DESC
    """,
}


def markdown_table(headers, rows) -> str:
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    REPORTS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    connection = duckdb.connect()
    parquet_path = str(SNAPSHOT).replace("\\", "/").replace("'", "''")
    connection.execute(f"CREATE VIEW snapshot AS SELECT * FROM read_parquet('{parquet_path}')")

    results = {}
    for name, query in QUERIES.items():
        cursor = connection.execute(query)
        headers = [item[0] for item in cursor.description]
        rows = cursor.fetchall()
        with (TABLES / f"{name}.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(headers)
            writer.writerows(rows)
        results[name] = (headers, rows)

    report = [
        "# Retention Analytics: January 31 Customer Snapshot",
        "",
        "These descriptive results use only the leakage-safe customer snapshot. They show association, not proof that one customer behaviour causes another.",
        "",
    ]
    for name, (headers, rows) in results.items():
        report.extend([f"## {name.replace('_', ' ').title()}", "", markdown_table(headers, rows), ""])

    (REPORTS / "retention_analytics_summary.md").write_text("\n".join(report), encoding="utf-8")
    print(f"Wrote analytics tables to {TABLES}")
    print(f"Wrote {REPORTS / 'retention_analytics_summary.md'}")


if __name__ == "__main__":
    main()
