from pathlib import Path
import sys

import polars as pl


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
INPUT = PROJECT_ROOT / "data" / "silver" / "customer_snapshot_2017-01-31.parquet"
OUTPUT = PROJECT_ROOT / "data" / "gold" / "model_input_2017-01-31.parquet"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    snapshot = pl.read_parquet(INPUT)

    model_input = snapshot.with_columns(
        # Categories are text labels, not larger/smaller numbers.
        pl.col("city").cast(pl.String).fill_null("unknown").alias("city_category"),
        pl.col("gender_clean").fill_null("unknown").alias("gender_category"),
        pl.col("registered_via").cast(pl.String).fill_null("unknown").alias("registration_channel_category"),
        pl.col("latest_payment_method_id").cast(pl.String).fill_null("unknown").alias("latest_payment_method_category"),
        pl.col("latest_plan_days").cast(pl.String).fill_null("unknown").alias("latest_plan_days_category"),

        # Keep missing numeric values as null for now. The ML pipeline will impute them
        # using training data only, so it cannot learn from the validation/test set.
        pl.col("age_unknown_flag").fill_null(1).cast(pl.Int8),
    ).drop(
        # Raw dates and numeric category IDs are not direct model inputs.
        "city",
        "gender_clean",
        "registered_via",
        "latest_payment_method_id",
        "latest_plan_days",
        "first_transaction_date",
        "last_transaction_date",
        "registration_date",
    )

    assert model_input.height == model_input["msno"].n_unique(), "Expected one row per customer."
    assert model_input["is_churn"].null_count() == 0, "Target label is required."

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    model_input.write_parquet(OUTPUT)

    print(f"Wrote {OUTPUT}")
    print(f"Rows: {model_input.height:,}")
    print("Columns:")
    for column in model_input.columns:
        print(f"- {column}: {model_input.schema[column]}")


if __name__ == "__main__":
    main()
