# Model Tournament

All models used the same training, calibration, and unseen test split. Because the project prioritizes a limited contact list, the winner is selected by top-10% lift, then probability reliability (lower Brier score), average precision, and ROC-AUC.

| model | test_customers | accuracy_at_50_percent_risk | precision_at_50_percent_risk | recall_at_50_percent_risk | roc_auc | average_precision | brier_score | top_10_percent_actual_churn | lift_at_top_10_percent |
|---|---|---|---|---|---|---|---|---|---|
| lightgbm_isotonic_calibrated | 194192 | 0.933514 | 0.766968 | 0.374614 | 0.868829 | 0.571582 | 0.054044 | 0.50793 | 5.647311 |
| catboost_isotonic_calibrated | 194192 | 0.932268 | 0.76347 | 0.357781 | 0.869718 | 0.563544 | 0.05467 | 0.507827 | 5.646166 |
| xgboost_isotonic_calibrated | 194192 | 0.932541 | 0.803616 | 0.330814 | 0.869868 | 0.567243 | 0.05449 | 0.506179 | 5.627846 |

## Selected model

**lightgbm_isotonic_calibrated** was selected for the campaign ranking.