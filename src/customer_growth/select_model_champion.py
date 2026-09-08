"""Select the deployable champion from completed tournament scores without retraining."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
REPORTS = PROJECT_ROOT / "reports"
PREDICTIONS = PROJECT_ROOT / "data" / "gold" / "test_predictions_model_tournament.parquet"


def markdown_table(frame: pd.DataFrame) -> str:
    headers = [str(column) for column in frame.columns]
    rows = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    rows.extend("| " + " | ".join(str(value) for value in row) + " |" for row in frame.itertuples(index=False, name=None))
    return "\n".join(rows)


def main() -> None:
    metrics = pd.read_csv(REPORTS / "model_tournament_metrics.csv").sort_values(
        ["lift_at_top_10_percent", "brier_score", "average_precision", "roc_auc"],
        ascending=[False, True, False, False],
    ).reset_index(drop=True)
    winner = metrics.iloc[0]
    model_to_probability = {
        "xgboost_isotonic_calibrated": "xgboost_calibrated_probability",
        "catboost_isotonic_calibrated": "catboost_calibrated_probability",
        "lightgbm_isotonic_calibrated": "lightgbm_calibrated_probability",
    }
    predictions = pd.read_parquet(PREDICTIONS)
    predictions["champion_calibrated_probability"] = predictions[model_to_probability[str(winner["model"])]]
    predictions.to_parquet(PREDICTIONS, index=False)
    (REPORTS / "model_tournament_metrics.csv").write_text(metrics.to_csv(index=False), encoding="utf-8")
    (REPORTS / "model_tournament_winner.json").write_text(
        json.dumps(
            {
                "selected_model": str(winner["model"]),
                "selection_rule": "highest top-10% lift; then lower Brier score; then average precision and ROC-AUC",
                "metrics": winner.to_dict(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    summary = [
        "# Model Tournament", "",
        "All models used the same training, calibration, and unseen test split. Because the project prioritizes a limited contact list, the winner is selected by top-10% lift, then probability reliability (lower Brier score), average precision, and ROC-AUC.", "",
        markdown_table(metrics), "",
        f"## Selected model\n\n**{winner['model']}** was selected for the campaign ranking.",
    ]
    (REPORTS / "model_tournament_summary.md").write_text("\n".join(summary), encoding="utf-8")
    print(f"Selected model: {winner['model']}")


if __name__ == "__main__":
    main()
