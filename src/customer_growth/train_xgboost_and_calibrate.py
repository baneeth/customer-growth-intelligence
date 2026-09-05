from pathlib import Path
import math
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score, brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder
from xgboost import XGBClassifier


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
INPUT = PROJECT_ROOT / "data" / "gold" / "model_input_2017-01-31.parquet"
MODELS = PROJECT_ROOT / "models"
REPORTS = PROJECT_ROOT / "reports"
PREDICTIONS = PROJECT_ROOT / "data" / "gold" / "test_predictions_xgboost.parquet"

RANDOM_STATE = 42
MODEL_TRAIN_ROWS = 200_000
CALIBRATION_ROWS = 100_000
# Business setting: change 10 to 15, 20, or another percentage based on campaign capacity.
CAMPAIGN_CAPACITY_PERCENT = 10

CATEGORICAL_FEATURES = [
    "city_category",
    "gender_category",
    "registration_channel_category",
    "latest_payment_method_category",
    "latest_plan_days_category",
]


def metrics(name: str, truth, probabilities) -> dict:
    truth = np.asarray(truth)
    probabilities = np.asarray(probabilities)
    top_count = math.ceil(len(truth) * 0.10)
    top_truth = truth[np.argsort(probabilities)[::-1][:top_count]]
    base_rate = truth.mean()
    return {
        "model": name,
        "test_customers": len(truth),
        "roc_auc": round(float(roc_auc_score(truth, probabilities)), 6),
        "average_precision": round(float(average_precision_score(truth, probabilities)), 6),
        "brier_score": round(float(brier_score_loss(truth, probabilities)), 6),
        "top_10_percent_actual_churn": round(float(top_truth.mean()), 6),
        "lift_at_top_10_percent": round(float(top_truth.mean() / base_rate), 6),
    }


def calibration_table(truth, probabilities) -> pd.DataFrame:
    frame = pd.DataFrame(
        {"actual_churn": np.asarray(truth), "predicted_risk": np.asarray(probabilities)}
    )
    frame["risk_band"] = pd.cut(frame["predicted_risk"], bins=np.linspace(0, 1, 11), include_lowest=True)
    return (
        frame.groupby("risk_band", observed=False)
        .agg(
            customers=("actual_churn", "size"),
            average_predicted_risk=("predicted_risk", "mean"),
            actual_churn_rate=("actual_churn", "mean"),
        )
        .reset_index()
    )


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    if not 0 < CAMPAIGN_CAPACITY_PERCENT <= 100:
        raise ValueError("CAMPAIGN_CAPACITY_PERCENT must be greater than 0 and no more than 100.")
    data = pd.read_parquet(INPUT)
    target = data.pop("is_churn")
    customer_ids = data.pop("msno")
    numeric_features = [column for column in data.columns if column not in CATEGORICAL_FEATURES]

    train_pool_x, test_x, train_pool_y, test_y, train_pool_ids, test_ids = train_test_split(
        data, target, customer_ids, test_size=0.20, stratify=target, random_state=RANDOM_STATE
    )
    model_x, remaining_x, model_y, remaining_y = train_test_split(
        train_pool_x,
        train_pool_y,
        train_size=MODEL_TRAIN_ROWS,
        stratify=train_pool_y,
        random_state=RANDOM_STATE,
    )
    calibration_x, _, calibration_y, _ = train_test_split(
        remaining_x,
        remaining_y,
        train_size=CALIBRATION_ROWS,
        stratify=remaining_y,
        random_state=RANDOM_STATE + 1,
    )

    preprocessor = ColumnTransformer(
        [
            (
                "numeric",
                Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=True))]),
                numeric_features,
            ),
            (
                "category",
                Pipeline(
                    [
                        ("impute", SimpleImputer(strategy="constant", fill_value="unknown")),
                        (
                            "ordinal",
                            OrdinalEncoder(
                                handle_unknown="use_encoded_value",
                                unknown_value=-1,
                                encoded_missing_value=-1,
                            ),
                        ),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
        ]
    )
    model_x_encoded = preprocessor.fit_transform(model_x)
    calibration_x_encoded = preprocessor.transform(calibration_x)
    test_x_encoded = preprocessor.transform(test_x)

    negative_to_positive_ratio = (model_y == 0).sum() / (model_y == 1).sum()
    xgb = XGBClassifier(
        n_estimators=350,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.80,
        colsample_bytree=0.80,
        min_child_weight=20,
        objective="binary:logistic",
        eval_metric="logloss",
        scale_pos_weight=negative_to_positive_ratio,
        tree_method="hist",
        n_jobs=-1,
        random_state=RANDOM_STATE,
    )
    xgb.fit(model_x_encoded, model_y)

    raw_calibration_probability = xgb.predict_proba(calibration_x_encoded)[:, 1]
    raw_test_probability = xgb.predict_proba(test_x_encoded)[:, 1]

    # Calibration learns how to translate raw model scores into more trustworthy probabilities.
    calibrator = IsotonicRegression(out_of_bounds="clip")
    calibrator.fit(raw_calibration_probability, calibration_y)
    calibrated_test_probability = calibrator.predict(raw_test_probability)

    results = pd.DataFrame(
        [
            metrics("xgboost_raw", test_y, raw_test_probability),
            metrics("xgboost_isotonic_calibrated", test_y, calibrated_test_probability),
        ]
    )
    calibration = calibration_table(test_y, calibrated_test_probability)
    top_count = math.ceil(
        len(calibrated_test_probability) * CAMPAIGN_CAPACITY_PERCENT / 100
    )
    top_indices = np.argsort(calibrated_test_probability)[::-1][:top_count]
    targeted = np.zeros(len(calibrated_test_probability), dtype=bool)
    targeted[top_indices] = True
    threshold = float(calibrated_test_probability[top_indices].min())
    threshold_summary = pd.DataFrame(
        [
            {
                "campaign_capacity": (
                    f"top {CAMPAIGN_CAPACITY_PERCENT} percent of customers by calibrated risk"
                ),
                "campaign_capacity_percent": CAMPAIGN_CAPACITY_PERCENT,
                "calibrated_risk_threshold": threshold,
                "customers_targeted": int(targeted.sum()),
                "actual_churn_rate_in_targeted_group": float(np.asarray(test_y)[targeted].mean()),
                "overall_test_churn_rate": float(np.asarray(test_y).mean()),
            }
        ]
    )

    feature_importance = pd.DataFrame(
        {
            "feature": preprocessor.get_feature_names_out(),
            "importance": xgb.feature_importances_,
        }
    ).sort_values("importance", ascending=False).head(20)

    MODELS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(preprocessor, MODELS / "xgboost_preprocessor.joblib")
    joblib.dump(xgb, MODELS / "xgboost_churn_model.joblib")
    joblib.dump(calibrator, MODELS / "xgboost_isotonic_calibrator.joblib")
    results.to_csv(REPORTS / "xgboost_model_metrics.csv", index=False)
    calibration.to_csv(REPORTS / "xgboost_calibration_table.csv", index=False)
    threshold_summary.to_csv(REPORTS / "xgboost_campaign_threshold.csv", index=False)
    feature_importance.to_csv(REPORTS / "xgboost_feature_importance.csv", index=False)
    pd.DataFrame(
        {
            "msno": test_ids.reset_index(drop=True),
            "is_churn": test_y.reset_index(drop=True),
            "xgboost_raw_probability": raw_test_probability,
            "xgboost_calibrated_probability": calibrated_test_probability,
        }
    ).to_parquet(PREDICTIONS, index=False)

    report = [
        "# XGBoost and Probability Calibration",
        "",
        f"XGBoost trained on {len(model_x):,} customers, calibrated on a separate {len(calibration_x):,} customers, and evaluated on {len(test_x):,} unseen customers.",
        "",
        "## Performance", "", dataframe_to_markdown(results),
        "", "## Calibration check", "", dataframe_to_markdown(calibration),
        "", "## Capacity-based campaign threshold", "", dataframe_to_markdown(threshold_summary),
        "", "## Most influential XGBoost inputs", "", dataframe_to_markdown(feature_importance),
    ]
    (REPORTS / "xgboost_calibration_summary.md").write_text("\n".join(report), encoding="utf-8")

    print(results.to_string(index=False))
    print("\nCampaign threshold")
    print(threshold_summary.to_string(index=False))
    print("\nTop XGBoost features")
    print(feature_importance.to_string(index=False))


if __name__ == "__main__":
    main()
