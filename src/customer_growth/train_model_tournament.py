"""Benchmark modern churn models on one fixed, leakage-safe evaluation split."""

from __future__ import annotations

import json
import math
from pathlib import Path

from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
INPUT = PROJECT_ROOT / "data" / "gold" / "model_input_2017-01-31.parquet"
REPORTS = PROJECT_ROOT / "reports"
OUTPUT = PROJECT_ROOT / "data" / "gold" / "test_predictions_model_tournament.parquet"
WINNER_OUTPUT = REPORTS / "model_tournament_winner.json"

RANDOM_STATE = 42
MODEL_TRAIN_ROWS = 200_000
CALIBRATION_ROWS = 100_000
CATEGORICAL_FEATURES = [
    "city_category",
    "gender_category",
    "registration_channel_category",
    "latest_payment_method_category",
    "latest_plan_days_category",
]


def score_model(name: str, truth: pd.Series, probabilities: np.ndarray) -> dict:
    """Return both business-facing and statistical checks on untouched customers."""
    probability = np.asarray(probabilities)
    prediction = probability >= 0.50
    top_count = math.ceil(len(truth) * 0.10)
    top_truth = np.asarray(truth)[np.argsort(probability)[::-1][:top_count]]
    base_rate = float(np.mean(truth))
    return {
        "model": name,
        "test_customers": len(truth),
        "accuracy_at_50_percent_risk": round(float(accuracy_score(truth, prediction)), 6),
        "precision_at_50_percent_risk": round(float(precision_score(truth, prediction, zero_division=0)), 6),
        "recall_at_50_percent_risk": round(float(recall_score(truth, prediction, zero_division=0)), 6),
        "roc_auc": round(float(roc_auc_score(truth, probability)), 6),
        "average_precision": round(float(average_precision_score(truth, probability)), 6),
        "brier_score": round(float(brier_score_loss(truth, probability)), 6),
        "top_10_percent_actual_churn": round(float(np.mean(top_truth)), 6),
        "lift_at_top_10_percent": round(float(np.mean(top_truth) / base_rate), 6),
    }


def calibrate_and_score(
    name: str,
    calibration_truth: pd.Series,
    calibration_probability: np.ndarray,
    test_truth: pd.Series,
    test_probability: np.ndarray,
) -> tuple[dict, np.ndarray]:
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(calibration_probability, calibration_truth)
    calibrated = calibrator.predict(test_probability)
    return score_model(name, test_truth, calibrated), calibrated


def main() -> None:
    data = pd.read_parquet(INPUT)
    target = data.pop("is_churn")
    customer_ids = data.pop("msno")

    train_pool_x, test_x, train_pool_y, test_y, _, test_ids = train_test_split(
        data, target, customer_ids, test_size=0.20, stratify=target, random_state=RANDOM_STATE
    )
    model_x, remaining_x, model_y, remaining_y = train_test_split(
        train_pool_x, train_pool_y, train_size=MODEL_TRAIN_ROWS,
        stratify=train_pool_y, random_state=RANDOM_STATE,
    )
    calibration_x, _, calibration_y, _ = train_test_split(
        remaining_x, remaining_y, train_size=CALIBRATION_ROWS,
        stratify=remaining_y, random_state=RANDOM_STATE + 1,
    )
    class_ratio = float((model_y == 0).sum() / (model_y == 1).sum())

    # CatBoost sees categories as categories, rather than as arbitrary ordered numbers.
    cat_model_x = model_x.copy()
    cat_calibration_x = calibration_x.copy()
    cat_test_x = test_x.copy()
    for column in CATEGORICAL_FEATURES:
        cat_model_x[column] = cat_model_x[column].fillna("unknown").astype(str)
        cat_calibration_x[column] = cat_calibration_x[column].fillna("unknown").astype(str)
        cat_test_x[column] = cat_test_x[column].fillna("unknown").astype(str)

    catboost = CatBoostClassifier(
        iterations=500,
        depth=7,
        learning_rate=0.05,
        loss_function="Logloss",
        eval_metric="AUC",
        class_weights=[1.0, class_ratio],
        random_seed=RANDOM_STATE,
        verbose=False,
        thread_count=-1,
    )
    catboost.fit(cat_model_x, model_y, cat_features=CATEGORICAL_FEATURES)
    cat_calibration_probability = catboost.predict_proba(cat_calibration_x)[:, 1]
    cat_test_probability = catboost.predict_proba(cat_test_x)[:, 1]
    cat_metrics, cat_calibrated = calibrate_and_score(
        "catboost_isotonic_calibrated", calibration_y, cat_calibration_probability, test_y, cat_test_probability
    )

    # LightGBM also receives categorical columns explicitly, using a separate copy.
    lgb_model_x = model_x.copy()
    lgb_calibration_x = calibration_x.copy()
    lgb_test_x = test_x.copy()
    for column in CATEGORICAL_FEATURES:
        categories = pd.concat([lgb_model_x[column], lgb_calibration_x[column], lgb_test_x[column]]).fillna("unknown").astype(str).unique()
        dtype = pd.CategoricalDtype(categories=categories)
        lgb_model_x[column] = lgb_model_x[column].fillna("unknown").astype(str).astype(dtype)
        lgb_calibration_x[column] = lgb_calibration_x[column].fillna("unknown").astype(str).astype(dtype)
        lgb_test_x[column] = lgb_test_x[column].fillna("unknown").astype(str).astype(dtype)

    lightgbm = LGBMClassifier(
        objective="binary",
        n_estimators=500,
        learning_rate=0.05,
        num_leaves=31,
        min_child_samples=20,
        subsample=0.80,
        colsample_bytree=0.80,
        reg_lambda=1.0,
        scale_pos_weight=class_ratio,
        random_state=RANDOM_STATE,
        n_jobs=-1,
        verbosity=-1,
    )
    lightgbm.fit(lgb_model_x, model_y, categorical_feature=CATEGORICAL_FEATURES)
    lgb_calibration_probability = lightgbm.predict_proba(lgb_calibration_x)[:, 1]
    lgb_test_probability = lightgbm.predict_proba(lgb_test_x)[:, 1]
    lgb_metrics, lgb_calibrated = calibrate_and_score(
        "lightgbm_isotonic_calibrated", calibration_y, lgb_calibration_probability, test_y, lgb_test_probability
    )

    # XGBoost was already trained on this exact split; reuse its persisted evaluation.
    xgb_metrics = pd.read_csv(REPORTS / "xgboost_model_metrics.csv")
    xgb_record = xgb_metrics.loc[xgb_metrics["model"] == "xgboost_isotonic_calibrated"].iloc[0].to_dict()
    xgb_predictions = pd.read_parquet(PROJECT_ROOT / "data" / "gold" / "test_predictions_xgboost.parquet")
    if not xgb_predictions["msno"].reset_index(drop=True).equals(test_ids.reset_index(drop=True)):
        raise ValueError("The persisted XGBoost predictions do not match the fixed tournament test split.")
    xgb_probability = xgb_predictions["xgboost_calibrated_probability"].to_numpy()
    xgb_full_metrics = score_model("xgboost_isotonic_calibrated", test_y, xgb_probability)
    # Preserve exact existing XGBoost ranking and calibration figures in the tournament table.
    xgb_full_metrics.update({key: xgb_record[key] for key in ["roc_auc", "average_precision", "brier_score", "top_10_percent_actual_churn", "lift_at_top_10_percent"]})

    # This is a contact-prioritisation problem. Select on concentration in the
    # top contact group first, then probability reliability and overall ranking.
    results = pd.DataFrame([xgb_full_metrics, cat_metrics, lgb_metrics]).sort_values(
        ["lift_at_top_10_percent", "brier_score", "average_precision", "roc_auc"], ascending=[False, True, False, False]
    ).reset_index(drop=True)
    winner = results.iloc[0]
    probability_columns = {
        "xgboost_isotonic_calibrated": xgb_probability,
        "catboost_isotonic_calibrated": cat_calibrated,
        "lightgbm_isotonic_calibrated": lgb_calibrated,
    }
    champion_probability = probability_columns[str(winner["model"])]
    predictions = pd.DataFrame(
        {
            "msno": test_ids.reset_index(drop=True),
            "is_churn": test_y.reset_index(drop=True),
            "xgboost_calibrated_probability": xgb_probability,
            "catboost_calibrated_probability": cat_calibrated,
            "lightgbm_calibrated_probability": lgb_calibrated,
            "champion_calibrated_probability": champion_probability,
        }
    )

    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(REPORTS / "model_tournament_metrics.csv", index=False)
    predictions.to_parquet(OUTPUT, index=False)
    WINNER_OUTPUT.write_text(
        json.dumps({"selected_model": str(winner["model"]), "selection_rule": "highest top-10% lift; then lower Brier score; then average precision and ROC-AUC", "metrics": winner.to_dict()}, indent=2),
        encoding="utf-8",
    )
    report = [
        "# Model Tournament", "",
        "All models used the same training, calibration, and unseen test split. Because this is a contact-prioritisation problem, the winner is chosen by top-10% lift, then probability reliability (lower Brier score), average precision, and ROC-AUC.", "",
        results.to_markdown(index=False), "",
        f"## Selected model\n\n**{winner['model']}** was selected for the campaign ranking.",
    ]
    (REPORTS / "model_tournament_summary.md").write_text("\n".join(report), encoding="utf-8")
    print(results.to_string(index=False))
    print(f"\nSelected model: {winner['model']}")


if __name__ == "__main__":
    main()
