"""Fast quality checks for the generated Customer Growth project artifacts."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CUTOFF = pd.Timestamp("2017-01-31")


def read_parquet(relative_path: str) -> pd.DataFrame:
    path = PROJECT_ROOT / relative_path
    assert path.exists(), f"Missing expected output: {path}"
    return pd.read_parquet(path)


def test_customer_snapshot_has_one_row_per_customer_and_no_future_transactions():
    snapshot = read_parquet("data/silver/customer_snapshot_2017-01-31.parquet")

    assert snapshot["msno"].is_unique
    assert snapshot["is_churn"].notna().all()
    assert set(snapshot["is_churn"].unique()) <= {0, 1}
    assert snapshot["last_transaction_date"].dropna().max() <= CUTOFF.date()
    assert 0.08 < snapshot["is_churn"].mean() < 0.10


def test_model_input_preserves_customer_grain_and_safe_categories():
    snapshot = read_parquet("data/silver/customer_snapshot_2017-01-31.parquet")
    model_input = read_parquet("data/gold/model_input_2017-01-31.parquet")

    assert model_input["msno"].is_unique
    assert len(model_input) == len(snapshot)
    assert set(model_input["msno"]) == set(snapshot["msno"])
    assert "latest_payment_method_id" not in model_input.columns
    assert "latest_payment_method_category" in model_input.columns
    assert "age_unknown_flag" in model_input.columns


def test_calibrated_probabilities_are_real_probabilities():
    predictions = read_parquet("data/gold/test_predictions_xgboost.parquet")

    probability = predictions["xgboost_calibrated_probability"]
    assert predictions["msno"].is_unique
    assert probability.notna().all()
    assert probability.between(0, 1).all()
    assert probability.nunique() > 100


def test_campaign_recommendation_is_affordable_and_best_feasible_option():
    reports = PROJECT_ROOT / "reports"
    config = json.loads((PROJECT_ROOT / "configs/campaign_scenario.json").read_text(encoding="utf-8"))
    options = pd.read_csv(reports / "campaign_spend_optimization.csv")
    recommended = pd.read_csv(reports / "campaign_spend_recommendation.csv")

    assert len(recommended) == 1
    chosen = recommended.iloc[0]
    feasible = options[options["within_budget"]]

    assert not feasible.empty
    assert chosen["campaign_spend"] <= config["maximum_campaign_budget"]
    assert chosen["scenario_net_value"] == feasible["scenario_net_value"].max()
    assert chosen["capacity_percent"] in set(config["capacity_grid_percent"])


def test_dashboard_contains_required_decision_visuals():
    dashboard = PROJECT_ROOT / "reports/executive_dashboard.html"
    assert dashboard.exists()
    html = dashboard.read_text(encoding="utf-8")

    required_titles = [
        "Churn is concentrated in the model",
        "Model comparison: ROC-AUC",
        "Churn rate by latest auto-renewal setting",
        "Churn rate by time since latest payment",
        "Churn rate by payment-history length",
        "Modeled net value by campaign size",
    ]
    assert all(title in html for title in required_titles)
    assert html.count("<svg") >= 6
