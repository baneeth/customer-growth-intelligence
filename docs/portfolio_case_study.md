# Customer Growth Decision Intelligence Platform

## Business question

A subscription business needs to decide which customers to contact before they leave, how many customers it can afford to contact, and whether a retention campaign is likely to create more value than it costs.

## What I built

I built a leakage-safe churn decision system using anonymized KKBox subscription data. The project converts transaction receipts and customer profiles into one customer-level snapshot, predicts churn risk, calibrates the predicted probabilities, ranks customers for retention outreach, and compares campaign sizes under editable business assumptions.

## Data and timeline design

- Population: 970,960 labeled customers.
- Churn rate: 8.99%.
- Prediction cutoff: January 31, 2017.
- Features: only information available on or before the cutoff.
- Future renewals and March listening activity: retained as raw/context data but excluded from the feature snapshot because they occur after the decision date.

This timeline rule prevents data leakage. In plain language, the model is not allowed to look at the future answer before making its prediction.

## Data engineering and quality decisions

- Preserved one row per customer in the final snapshot, despite transactions having many receipt rows per customer.
- Verified source coverage and switched from the smaller refresh transaction file to the full historical transaction file when the refresh file did not cover enough labeled customers.
- Kept unusual cancellation and long-plan records, then created flags rather than deleting data without evidence.
- Treated invalid ages as unknown and retained missingness indicators.
- Added automated checks for customer grain, cutoff-safe dates, model-input contracts, probability ranges, campaign logic, and dashboard completeness.

## Business insights

- Latest auto-renewal off: 38.70% observed churn versus 4.67% when it is on.
- Last payment more than 90 days before the cutoff: 71.60% observed churn.
- One to three historical payments: 22.45% observed churn versus 5.21% for 26 or more payments.

These are predictive associations, not causal claims.

## Model results

All models were evaluated on the same 194,192 unseen customers.

| Model | ROC-AUC | Top-10% lift |
|---|---:|---:|
| Logistic Regression | 0.824 | 5.15x |
| Random Forest | 0.862 | 5.52x |
| Calibrated XGBoost | 0.870 | 5.63x |

The calibrated XGBoost model was selected because it had the strongest ranking performance and its probabilities were adjusted to better reflect real churn frequency. The observed churn rate in the highest-risk 10% was 50.62%, compared with 8.99% overall.

## Decision support and campaign economics

The model ranks every customer; campaign size is a business capacity decision, not a fixed property of the model. The optimizer tests campaign sizes, applies a budget, calculates expected churners from calibrated probabilities, estimates a break-even save rate, and selects the feasible option with the highest modeled net value.

Under the current illustrative assumptions (30-unit offer cost, 10% save rate, six retained months, and a 1,000,000-unit budget), the recommended campaign targets the top 5%:

- 9,710 customers contacted.
- 291,300 units campaign spend.
- 71.46% average calibrated churn risk.
- 1.11% break-even save rate.
- 2,323,914 units modeled net value.

The value and return figures are scenarios, not realized profit. A real company would validate the offer through a controlled experiment with a holdout group.

## Deliverables

- Reusable Python scripts for snapshot building, analytics, model training, calibration, campaign optimization, and dashboard generation.
- Reusable SQL analytics queries.
- An executive dashboard with six focused visuals.
- Automated tests: `python -m pytest -q`.
- Editable campaign assumptions in `configs/campaign_scenario.json`.

## Responsible limitations

- This is an anonymized competition dataset, not a live company system.
- The dataset does not provide verified profit or lifetime value; subscription payment is used as an editable value proxy.
- Predictive patterns do not establish causation.
- Production use would require privacy review, eligibility rules, offer experimentation, monitoring, and incremental-lift measurement.
