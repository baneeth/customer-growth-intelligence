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


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def evaluate_capacity(frame: pd.DataFrame, capacity_percent: float, config: dict) -> dict:
    target_count = math.ceil(len(frame) * capacity_percent / 100)
    target = frame.head(target_count)
    expected_churners = target["xgboost_calibrated_probability"].sum()
    value_per_churner = target["monthly_value_proxy"].mean() * config["value_months"]
    spend = target_count * config["offer_cost_per_customer"]
    expected_saved = expected_churners * config["assumed_save_rate"]
    retained_value = expected_saved * value_per_churner
    break_even_save_rate = (
        spend / (expected_churners * value_per_churner)
        if expected_churners > 0 and value_per_churner > 0
        else None
    )
    return {
        "capacity_percent": capacity_percent,
        "customers_targeted": target_count,
        "campaign_spend": round(spend, 2),
        "within_budget": spend <= config["maximum_campaign_budget"],
        "average_calibrated_risk": round(target["xgboost_calibrated_probability"].mean(), 4),
        "expected_churners": round(expected_churners, 1),
        "assumed_save_rate_percent": round(config["assumed_save_rate"] * 100, 2),
        "break_even_save_rate_percent": round(break_even_save_rate * 100, 2),
        "expected_saved_customers": round(expected_saved, 1),
        "value_per_saved_customer": round(value_per_churner, 2),
        "scenario_retained_value": round(retained_value, 2),
        "scenario_net_value": round(retained_value - spend, 2),
        "scenario_roi": round((retained_value - spend) / spend, 4) if spend else None,
    }


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    with CONFIG.open(encoding="utf-8") as file:
        config = json.load(file)

    for name in ["offer_cost_per_customer", "maximum_campaign_budget", "value_proxy_multiplier"]:
        if config[name] < 0:
            raise ValueError(f"{name} must not be negative.")
    if not 0 <= config["assumed_save_rate"] <= 1:
        raise ValueError("assumed_save_rate must be between 0 and 1.")

    predictions = pd.read_parquet(PREDICTIONS)
    value_data = pd.read_parquet(MODEL_INPUT)[["msno", "latest_amount_paid", "average_amount_paid"]]
    ranked = predictions.merge(value_data, on="msno", how="left", validate="one_to_one")
    ranked["monthly_value_proxy"] = (
        ranked["latest_amount_paid"]
        .where(ranked["latest_amount_paid"].notna(), ranked["average_amount_paid"])
        .fillna(0)
        * config["value_proxy_multiplier"]
    )
    ranked = ranked.sort_values("xgboost_calibrated_probability", ascending=False)

    results = pd.DataFrame(
        [evaluate_capacity(ranked, capacity, config) for capacity in config["capacity_grid_percent"]]
    )
    feasible = results[results["within_budget"]]
    if feasible.empty:
        recommendation = None
    else:
        recommendation = feasible.loc[feasible["scenario_net_value"].idxmax()].to_frame().T

    REPORTS.mkdir(parents=True, exist_ok=True)
    results.to_csv(REPORTS / "campaign_spend_optimization.csv", index=False)
    if recommendation is not None:
        recommendation.to_csv(REPORTS / "campaign_spend_recommendation.csv", index=False)

    report = [
        "# Campaign Spend Optimization",
        "",
        "## Interpretation boundary",
        "",
        "This analysis uses model-estimated churn risk plus editable business assumptions. It is not realized campaign profit. Validate the selected offer and audience through an experiment before operational rollout.",
        "",
        f"Monetary unit label: **{config['monetary_unit_label']}**. Value proxy multiplier: **{config['value_proxy_multiplier']}**.",
        "",
        f"Maximum campaign budget: **{config['maximum_campaign_budget']:,.2f} {config['monetary_unit_label']}**.",
        "",
        "## Capacity options",
        "",
        markdown_table(results),
    ]
    if recommendation is not None:
        report.extend([
            "", "## Recommended scenario under the configured budget", "", markdown_table(recommendation),
            "", "The recommended option is the capacity grid row with the highest scenario net value while remaining within the configured budget.",
        ])
    else:
        report.extend(["", "No capacity option fits the configured budget. Adjust the budget, offer cost, or capacity grid."])
    (REPORTS / "campaign_spend_optimization.md").write_text("\n".join(report), encoding="utf-8")

    print(results.to_string(index=False))
    if recommendation is not None:
        print("\nRecommended scenario")
        print(recommendation.to_string(index=False))


if __name__ == "__main__":
    main()
