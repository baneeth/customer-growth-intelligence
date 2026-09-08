# Customer Growth Decision Intelligence Platform

An end-to-end churn analytics and retention-prioritization project built with anonymized KKBox subscription data. It answers a practical question:

> Given a limited retention budget, which customers should a subscription business contact first, and why?

## Live portfolio

- Dashboard: https://customer-growth-intelligence-q65qndouk-baneeths-projects.vercel.app
- Source code: https://github.com/baneeth/customer-growth-intelligence

## Business outcome

The project converts raw subscription receipts and customer profiles into one leakage-safe row per customer, predicts churn risk, calibrates risk probabilities, and produces a capacity-based campaign priority list.

The model ranks every customer. Campaign capacity is a business choice: target the top 5%, 10%, 15%, 20%, or another percentage depending on available budget and staff.

## Results from the held-out test population

All models were evaluated on the same 194,192 unseen customers.

| Model | Accuracy at 50% risk | ROC-AUC | Top-10% lift |
|---|---:|---:|---:|
| Calibrated XGBoost | 93.25% | **0.870** | 5.63x |
| Calibrated CatBoost | 93.23% | 0.870 | 5.65x |
| Calibrated LightGBM | **93.35%** | 0.869 | **5.65x** |

LightGBM was selected for campaign ranking because it concentrated the most observed churn in the highest-risk 10% (50.79%), had the best probability reliability, and achieved the best accuracy and average precision. XGBoost had a very slightly higher overall ROC-AUC (0.870 versus 0.869). This is why the winner is selected using contact-list performance first, rather than AUC alone.

## How the business would use it

1. Score and rank every eligible customer.
2. Set campaign capacity in `configs/campaign_scenario.json`.
3. Contact only the highest-risk customers within that capacity.
4. Use the scenario model to compare campaign cost, assumed save rate, unit value, and retained-value assumptions.
5. Validate the real campaign through a controlled experiment before treating scenario value as realized value.

## Data timeline and leakage control

The most important design rule is: a model may only use information known at prediction time.

- Feature cutoff: January 31, 2017.
- Transaction features: payment history on or before the cutoff only.
- Later renewals/churn outcomes: labels for evaluation, never model inputs.
- March listening activity: retained as raw data but excluded from this January snapshot because it belongs to the future outcome period.
- Customer profiles registered after the cutoff: excluded from feature values.

## Pipeline

```text
raw source data
  -> profiling and source-coverage checks
  -> leakage-safe customer snapshot (one row per customer)
  -> model input with safe categories and missingness signals
  -> modern-model tournament: XGBoost, CatBoost, and LightGBM
  -> probability calibration
  -> ranked campaign priority list and scenario analysis
```

## Key findings

- Latest auto-renewal off: 38.70% observed churn vs. 4.67% when on.
- Last payment over 90 days before the cutoff: 71.60% observed churn.
- One to three historical payments: 22.45% observed churn vs. 5.21% for 26+ payments.
- The strongest first-pass model signals include recent payment amount, latest auto-renewal status, recent transaction count, and payment recency.

These are predictive associations, not claims of causation.

## Scenario assumptions

Campaign economics are intentionally separated from observed results. Edit `configs/campaign_scenario.json` to change:

- `campaign_capacity_percent`
- `offer_cost_per_customer`
- `assumed_save_rate`
- `value_months`
- `monetary_unit_label` (for example, USD, INR, or "dataset currency units")
- `value_proxy_multiplier` (converts the dataset price proxy to an estimated business unit value)
- `maximum_campaign_budget`
- `capacity_grid_percent` (the campaign sizes compared for the recommendation)

The spend optimizer chooses the capacity-grid option with the largest scenario net value that fits the budget. Under the default illustrative assumptions, the 5% option targets 9,710 customers, costs 291,300 dataset currency units, and has the highest scenario net value. This is a planning recommendation, not realized profit.

## Project structure

```text
configs/                     Editable campaign assumptions
data/landing/                Downloaded archives
data/raw/                    Immutable extracted source files
data/silver/                 Leakage-safe customer snapshot
data/gold/                   Model inputs, test predictions, campaign priority list
src/customer_growth/         Reusable Python pipeline code
sql/                         Reusable retention analysis queries
reports/                     Metrics, calibration, analytics, and scenario reports
docs/                        Business brief, roadmap, and interview notes
```

## Main scripts

```powershell
# Build the January 31 customer snapshot
python src/customer_growth/build_customer_snapshot.py

# Prepare clean model input
python src/customer_growth/prepare_model_data.py

# Run SQL-style retention analytics
python src/customer_growth/build_analytics.py

# Train Logistic Regression and Random Forest
python src/customer_growth/train_baseline_models.py

# Train the initial XGBoost benchmark and calibration reports
python src/customer_growth/train_xgboost_and_calibrate.py

# Run CatBoost and LightGBM on the same split, then select the campaign champion
python src/customer_growth/train_model_tournament.py

# Build capacity and campaign-economics scenario outputs
python src/customer_growth/build_campaign_decision_support.py

# Compare campaign sizes, budget, break-even save rate, and scenario value
python src/customer_growth/optimize_campaign_spend.py

# Build the executive dashboard with six decision visuals
python src/customer_growth/build_dashboard.py

# Run the automated project quality checks
python -m pytest -q
```

## Important reports

- `reports/retention_analytics_summary.md`
- `reports/baseline_model_summary.md`
- `reports/xgboost_calibration_summary.md`
- `reports/model_tournament_summary.md`
- `reports/model_tournament_metrics.csv`
- `reports/model_tournament_winner.json`
- `reports/campaign_decision_support.md`
- `reports/campaign_spend_optimization.md`
- `reports/campaign_spend_recommendation.csv`
- `reports/executive_dashboard.html`

## Automated quality checks

`tests/test_project_artifacts.py` checks the most important project contracts: one customer per row, cutoff-safe transaction dates, safe model categories, valid calibrated probabilities, an affordable and optimal campaign recommendation, and the required decision visuals in the dashboard.

## Reproducing the project

1. Create and activate a Python 3.11 virtual environment.
2. Install packages with `python -m pip install -r requirements.txt`.
3. Download the Kaggle source archives locally. The raw source data, trained model files, and generated parquet datasets are intentionally excluded from version control because they are large and/or source-restricted.
4. Run the scripts in the order listed above, then run `python -m pytest -q`.

## GitHub publishing boundary

The `.gitignore` file excludes local environments, Kaggle credentials, raw data, generated parquet files, trained model binaries, and personal learning materials. Publish the source code, SQL, configuration, report summaries, dashboard builder, tests, public case study, public business brief, and README; do not publish Kaggle credentials, source-restricted raw data, or personal learning notes.

## Limitations and responsible interpretation

- The project is an analytical training artifact based on anonymized competition data.
- The observed churn label does not prove that any feature causes churn.
- Scenario ROI depends on assumptions; it is not realized campaign revenue.
- A real business rollout requires holdout experimentation, operational eligibility checks, consent/privacy review, and measurement of incremental retention.
