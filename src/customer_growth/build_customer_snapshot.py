from datetime import date
from pathlib import Path
import sys

import polars as pl


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
TRANSACTIONS = PROJECT_ROOT / "data" / "raw" / "kkbox-2017" / "transactions.csv"
MEMBERS = PROJECT_ROOT / "data" / "raw" / "kkbox-2017" / "members_v3.csv"
LABELS = PROJECT_ROOT / "data" / "raw" / "kkbox-2017" / "data" / "churn_comp_refresh" / "train_v2.csv"
OUTPUT = PROJECT_ROOT / "data" / "silver" / "customer_snapshot_2017-01-31.parquet"

CUTOFF = date(2017, 1, 31)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    cutoff = pl.lit(CUTOFF).cast(pl.Date)

    transactions = pl.scan_csv(TRANSACTIONS).with_columns(
        pl.col("transaction_date")
        .cast(pl.String)
        .str.strptime(pl.Date, "%Y%m%d", strict=False)
        .alias("transaction_date_parsed"),
        pl.col("membership_expire_date")
        .cast(pl.String)
        .str.strptime(pl.Date, "%Y%m%d", strict=False)
        .alias("membership_expire_date_parsed"),
    )

    # This filter is the leakage guard: no transaction after January 31 is used.
    history = transactions.filter(pl.col("transaction_date_parsed") <= cutoff)

    overall_features = history.group_by("msno").agg(
        pl.len().alias("transaction_count_to_cutoff"),
        pl.col("transaction_date_parsed").min().alias("first_transaction_date"),
        pl.col("transaction_date_parsed").max().alias("last_transaction_date"),
        pl.col("payment_method_id").n_unique().alias("payment_method_count"),
        pl.col("payment_plan_days").n_unique().alias("plan_type_count"),
        pl.col("actual_amount_paid").sum().alias("total_amount_paid"),
        pl.col("actual_amount_paid").mean().alias("average_amount_paid"),
        pl.col("plan_list_price").sum().alias("total_list_price"),
        pl.col("is_auto_renew").mean().alias("auto_renew_rate"),
        pl.col("is_cancel").sum().alias("cancellation_count"),
        pl.col("is_cancel").mean().alias("cancellation_rate"),
    ).with_columns(
        (cutoff - pl.col("first_transaction_date"))
        .dt.total_days()
        .alias("days_since_first_transaction"),
        (cutoff - pl.col("last_transaction_date"))
        .dt.total_days()
        .alias("days_since_last_transaction"),
        (pl.col("total_list_price") - pl.col("total_amount_paid"))
        .alias("total_discount_amount"),
        pl.when(pl.col("total_list_price") > 0)
        .then((pl.col("total_list_price") - pl.col("total_amount_paid")) / pl.col("total_list_price"))
        .otherwise(None)
        .alias("discount_rate"),
    )

    recent_30_features = (
        history.filter(pl.col("transaction_date_parsed") >= pl.date(2017, 1, 1))
        .group_by("msno")
        .agg(
            pl.len().alias("transaction_count_last_31_days"),
            pl.col("actual_amount_paid").sum().alias("amount_paid_last_31_days"),
            pl.col("is_cancel").sum().alias("cancellations_last_31_days"),
        )
    )

    recent_90_features = (
        history.filter(pl.col("transaction_date_parsed") >= pl.date(2016, 11, 3))
        .group_by("msno")
        .agg(pl.len().alias("transaction_count_last_90_days"))
    )

    # For same-day subscription/cancellation events, cancellation is ordered last.
    latest_transaction_features = (
        history.sort(
            [
                "msno",
                "transaction_date_parsed",
                "is_cancel",
                "membership_expire_date_parsed",
            ]
        )
        .group_by("msno")
        .agg(
            pl.col("payment_method_id").last().alias("latest_payment_method_id"),
            pl.col("payment_plan_days").last().alias("latest_plan_days"),
            pl.col("plan_list_price").last().alias("latest_list_price"),
            pl.col("actual_amount_paid").last().alias("latest_amount_paid"),
            pl.col("is_auto_renew").last().alias("latest_is_auto_renew"),
            pl.col("is_cancel").last().alias("latest_is_cancel"),
        )
    )

    member_records = pl.scan_csv(MEMBERS).with_columns(
        pl.col("registration_init_time")
        .cast(pl.String)
        .str.strptime(pl.Date, "%Y%m%d", strict=False)
        .alias("registration_date")
    ).with_columns(
        pl.when(pl.col("bd").is_between(10, 100))
        .then(pl.col("bd"))
        .otherwise(None)
        .alias("age_clean"),
        (~pl.col("bd").is_between(10, 100)).cast(pl.Int8).alias("age_unknown_flag"),
        pl.col("gender").fill_null("unknown").alias("gender_clean"),
    )

    # A profile created after the cutoff did not exist when the prediction was made.
    members = member_records.select(
        "msno",
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("city"))
        .otherwise(None)
        .alias("city"),
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("age_clean"))
        .otherwise(None)
        .alias("age_clean"),
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("age_unknown_flag"))
        .otherwise(None)
        .alias("age_unknown_flag"),
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("gender_clean"))
        .otherwise(None)
        .alias("gender_clean"),
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("registered_via"))
        .otherwise(None)
        .alias("registered_via"),
        pl.when(pl.col("registration_date") <= cutoff)
        .then(pl.col("registration_date"))
        .otherwise(None)
        .alias("registration_date"),
    )

    # Keep every labelled customer: missing history is itself useful operational information.
    snapshot = (
        pl.scan_csv(LABELS)
        .join(overall_features, on="msno", how="left")
        .join(recent_30_features, on="msno", how="left")
        .join(recent_90_features, on="msno", how="left")
        .join(latest_transaction_features, on="msno", how="left")
        .join(members, on="msno", how="left")
        .with_columns(
            pl.col("transaction_count_to_cutoff").is_not_null().cast(pl.Int8).alias("has_transaction_history_flag"),
            pl.col("city").is_not_null().cast(pl.Int8).alias("has_member_profile_flag"),
            (cutoff - pl.col("registration_date"))
            .dt.total_days()
            .alias("days_since_registration"),
        )
        .with_columns(
            pl.col("transaction_count_to_cutoff").fill_null(0),
            pl.col("payment_method_count").fill_null(0),
            pl.col("plan_type_count").fill_null(0),
            pl.col("total_amount_paid").fill_null(0),
            pl.col("cancellation_count").fill_null(0),
            pl.col("transaction_count_last_31_days").fill_null(0),
            pl.col("amount_paid_last_31_days").fill_null(0),
            pl.col("cancellations_last_31_days").fill_null(0),
            pl.col("transaction_count_last_90_days").fill_null(0),
        )
    )

    result = snapshot.collect()
    assert result.height == result["msno"].n_unique(), "Snapshot must have one row per customer."
    assert result["is_churn"].null_count() == 0, "Every snapshot row needs a churn label."
    assert result["last_transaction_date"].drop_nulls().max() <= CUTOFF, "Future transaction leakage detected."

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    result.write_parquet(OUTPUT)
    print(f"Wrote {OUTPUT}")
    print(
        result.select(
            pl.len().alias("customers"),
            pl.col("msno").n_unique().alias("unique_customers"),
            pl.col("has_transaction_history_flag").sum().alias("customers_with_safe_history"),
            pl.col("has_member_profile_flag").sum().alias("customers_with_profile"),
            pl.col("is_churn").mean().alias("churn_rate"),
        )
    )


if __name__ == "__main__":
    main()
