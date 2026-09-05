from pathlib import Path
import json
import math
import sys

import pandas as pd


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
MODEL_INPUT = PROJECT_ROOT / "data" / "gold" / "model_input_2017-01-31.parquet"
PREDICTIONS = PROJECT_ROOT / "data" / "gold" / "test_predictions_xgboost.parquet"
CONFIG = PROJECT_ROOT / "configs" / "campaign_scenario.json"
REPORTS = PROJECT_ROOT / "reports"
OUTPUT = PROJECT_ROOT / "data" / "gold" / "campaign_priority_list.parquet"


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def scenario_summary(frame: pd.DataFrame, capacity_percent: float, save_rate: float, offer_cost: float, value_months: int) -> dict:
    target_count = math.ceil(len(frame) * capacity_percent / 100)
    priority = frame.nlargest(target_count, "xgboost_calibrated_probability")
    expected_churners = priority["xgboost_calibrated_probability"].sum()
    value_proxy = priority["monthly_value_proxy"].mean()
    expected_saved_customers = expected_churners * save_rate
    expected_retained_value = expected_saved_customers * value_proxy * value_months
    campaign_cost = target_count * offer_cost
    net_value = expected_retained_value - campaign_cost
    return {
        "campaign_capacity_percent": capacity_percent,
        "assumed_save_rate_percent": round(save_rate * 100, 2),
        "customers_targeted": target_count,
        "average_calibrated_risk": round(priority["xgboost_calibrated_probability"].mean(), 4),
        "expected_churners_from_model": round(expected_churners, 1),
        "average_monthly_value_proxy": round(value_proxy, 2),
        "offer_cost_per_customer": offer_cost,
        "value_months": value_months,
        "expected_saved_customers": round(expected_saved_customers, 1),
        "scenario_retained_value": round(expected_retained_value, 2),
        "campaign_cost": round(campaign_cost, 2),
        "scenario_net_value": round(net_value, 2),
        "scenario_roi": round(net_value / campaign_cost, 4) if campaign_cost else None,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with CONFIG.open(encoding="utf-8") as file:
        config = json.load(file)

    predictions = pd.read_parquet(PREDICTIONS)
    values = pd.read_parquet(MODEL_INPUT)[["msno", "latest_amount_paid", "average_amount_paid"]]
    frame = predictions.merge(values, on="msno", how="left", validate="one_to_one")
    frame["monthly_value_proxy"] = frame["latest_amount_paid"].where(
        frame["latest_amount_paid"].notna(), frame["average_amount_paid"]
    ).fillna(0)

    capacity = config["campaign_capacity_percent"]
    if not 0 < capacity <= 100:
        raise ValueError("campaign_capacity_percent must be between 0 and 100.")
    selected_count = math.ceil(len(frame) * capacity / 100)
    priority = frame.nlargest(selected_count, "xgboost_calibrated_probability").copy()
    priority["risk_rank"] = range(1, len(priority) + 1)
    priority["campaign_capacity_percent"] = capacity
    # The actual test label is excluded from the deployable list.
    deployable_priority = priority.drop(columns=["is_churn"])

    main_scenario = pd.DataFrame(
        [
            scenario_summary(
                frame,
                capacity,
                config["assumed_save_rate"],
                config["offer_cost_per_customer"],
                config["value_months"],
            )
        ]
    )
    sensitivity_rows = []
    for capacity_option in config["sensitivity_capacity_percent"]:
        for save_rate_option in config["sensitivity_save_rates"]:
            sensitivity_rows.append(
                scenario_summary(
                    frame,
                    capacity_option,
                    save_rate_option,
                    config["offer_cost_per_customer"],
                    config["value_months"],
                )
            )
    sensitivity = pd.DataFrame(sensitivity_rows).sort_values(
        ["campaign_capacity_percent", "assumed_save_rate_percent"]
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    deployable_priority.to_parquet(OUTPUT, index=False)
    main_scenario.to_csv(REPORTS / "campaign_value_scenario.csv", index=False)
    sensitivity.to_csv(REPORTS / "campaign_sensitivity.csv", index=False)

    report = [
        "# Retention Campaign Decision Support",
        "",
        "## Important interpretation",
        "",
        "This is a scenario model, not an observed campaign result. Offer cost, save rate, and value months are explicit assumptions in `configs/campaign_scenario.json`. Model scores estimate churn risk; they do not prove an offer will save every targeted customer.",
        "",
        "## Main scenario",
        "",
        markdown_table(main_scenario),
        "",
        "## Sensitivity analysis",
        "",
        markdown_table(sensitivity),
        "",
        "## Operational use",
        "",
        f"The deployable priority list contains the highest-risk {capacity}% of test customers ({selected_count:,} rows). It excludes the later churn label, because that label is unavailable when a real campaign is sent.",
    ]
    (REPORTS / "campaign_decision_support.md").write_text("\n".join(report), encoding="utf-8")

    print(main_scenario.to_string(index=False))
    print("\nSensitivity analysis")
    print(sensitivity.to_string(index=False))
    print(f"\nWrote {OUTPUT}")


if __name__ == "__main__":
    main()
