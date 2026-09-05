from pathlib import Path
import json
import math
import sys

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
INPUT = PROJECT_ROOT / "data" / "gold" / "model_input_2017-01-31.parquet"
MODELS = PROJECT_ROOT / "models"
REPORTS = PROJECT_ROOT / "reports"
PREDICTIONS = PROJECT_ROOT / "data" / "gold" / "test_predictions_baselines.parquet"

RANDOM_STATE = 42
MAX_TRAIN_ROWS = 200_000

CATEGORICAL_FEATURES = [
    "city_category",
    "gender_category",
    "registration_channel_category",
    "latest_payment_method_category",
    "latest_plan_days_category",
]


def make_preprocessor(numeric_features: list[str]) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
        ]
    )
    category_pipeline = Pipeline(
        [
            ("impute", SimpleImputer(strategy="constant", fill_value="unknown")),
            ("one_hot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, numeric_features),
            ("category", category_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def evaluate(name: str, truth: pd.Series, probabilities) -> dict[str, float]:
    predictions = (probabilities >= 0.50).astype(int)
    top_count = math.ceil(len(truth) * 0.10)
    top_truth = truth.iloc[probabilities.argsort()[::-1][:top_count]]
    base_rate = truth.mean()
    return {
        "model": name,
        "test_customers": int(len(truth)),
        "base_churn_rate": round(float(base_rate), 6),
        "roc_auc": round(float(roc_auc_score(truth, probabilities)), 6),
        "average_precision": round(float(average_precision_score(truth, probabilities)), 6),
        "precision_at_0_50": round(float(precision_score(truth, predictions, zero_division=0)), 6),
        "recall_at_0_50": round(float(recall_score(truth, predictions, zero_division=0)), 6),
        "accuracy_at_0_50": round(float(accuracy_score(truth, predictions)), 6),
        "top_10_percent_churn_rate": round(float(top_truth.mean()), 6),
        "lift_at_top_10_percent": round(float(top_truth.mean() / base_rate), 6),
    }


def dataframe_to_markdown(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for row in frame.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join(lines)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    data = pd.read_parquet(INPUT)
    target = data.pop("is_churn")
    customer_ids = data.pop("msno")
    numeric_features = [column for column in data.columns if column not in CATEGORICAL_FEATURES]

    train_pool_x, test_x, train_pool_y, test_y, train_pool_ids, test_ids = train_test_split(
        data,
        target,
        customer_ids,
        test_size=0.20,
        random_state=RANDOM_STATE,
        stratify=target,
    )

    # Same stratified sample for both models keeps their comparison fair and fast.
    if len(train_pool_x) > MAX_TRAIN_ROWS:
        train_x, _, train_y, _, = train_test_split(
            train_pool_x,
            train_pool_y,
            train_size=MAX_TRAIN_ROWS,
            random_state=RANDOM_STATE,
            stratify=train_pool_y,
        )
    else:
        train_x, train_y = train_pool_x, train_pool_y

    logistic = Pipeline(
        [
            ("preprocessor", make_preprocessor(numeric_features)),
            (
                "model",
                LogisticRegression(
                    solver="lbfgs",
                    class_weight="balanced",
                    max_iter=200,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    logistic.fit(train_x, train_y)
    logistic_probability = logistic.predict_proba(test_x)[:, 1]

    forest = Pipeline(
        [
            ("preprocessor", make_preprocessor(numeric_features)),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=75,
                    max_depth=12,
                    min_samples_leaf=75,
                    max_features="sqrt",
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )
    forest.fit(train_x, train_y)
    forest_probability = forest.predict_proba(test_x)[:, 1]

    metrics = [
        evaluate("logistic_regression", test_y.reset_index(drop=True), logistic_probability),
        evaluate("random_forest", test_y.reset_index(drop=True), forest_probability),
    ]

    feature_names = forest.named_steps["preprocessor"].get_feature_names_out()
    importance = pd.DataFrame(
        {
            "feature": feature_names,
            "importance": forest.named_steps["model"].feature_importances_,
        }
    ).sort_values("importance", ascending=False).head(20)

    MODELS.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    joblib.dump(logistic, MODELS / "logistic_regression_baseline.joblib")
    joblib.dump(forest, MODELS / "random_forest_baseline.joblib")
    pd.DataFrame(metrics).to_csv(REPORTS / "baseline_model_metrics.csv", index=False)
    importance.to_csv(REPORTS / "random_forest_feature_importance.csv", index=False)
    pd.DataFrame(
        {
            "msno": test_ids.reset_index(drop=True),
            "is_churn": test_y.reset_index(drop=True),
            "logistic_churn_probability": logistic_probability,
            "random_forest_churn_probability": forest_probability,
        }
    ).to_parquet(PREDICTIONS, index=False)

    lines = [
        "# Baseline Churn Models",
        "",
        f"Both models trained on the same stratified sample of {len(train_x):,} customers and were evaluated on {len(test_x):,} unseen customers.",
        "",
        "## Model metrics",
        "",
        dataframe_to_markdown(pd.DataFrame(metrics)),
        "",
        "## Random Forest: most influential features",
        "",
        dataframe_to_markdown(importance),
        "",
        "Metrics are descriptive first-pass results. Calibration and threshold selection are separate next steps.",
    ]
    (REPORTS / "baseline_model_summary.md").write_text("\n".join(lines), encoding="utf-8")

    print(pd.DataFrame(metrics).to_string(index=False))
    print("\nTop Random Forest features")
    print(importance.to_string(index=False))


if __name__ == "__main__":
    main()
