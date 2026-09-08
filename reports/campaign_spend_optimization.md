# Campaign Spend Optimization

## Interpretation boundary

This analysis uses model-estimated churn risk plus editable business assumptions. It is not realized campaign profit. Validate the selected offer and audience through an experiment before operational rollout.

Monetary unit label: **dataset currency units**. Value proxy multiplier: **1.0**.

Maximum campaign budget: **1,000,000.00 dataset currency units**.

## Capacity options

| capacity_percent | customers_targeted | campaign_spend | within_budget | average_calibrated_risk | expected_churners | assumed_save_rate_percent | break_even_save_rate_percent | expected_saved_customers | value_per_saved_customer | scenario_retained_value | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1942 | 58260.0 | True | 0.9499 | 1844.7 | 10.0 | 0.87 | 184.5 | 3625.06 | 668730.3 | 610470.3 | 10.4784 |
| 2 | 3884 | 116520.0 | True | 0.9129 | 3545.8 | 10.0 | 0.64 | 354.6 | 5160.53 | 1829846.38 | 1713326.38 | 14.7041 |
| 5 | 9710 | 291300.0 | True | 0.7253 | 7042.7 | 10.0 | 1.13 | 704.3 | 3646.15 | 2567888.22 | 2276588.22 | 7.8153 |
| 10 | 19420 | 582600.0 | True | 0.5111 | 9925.7 | 10.0 | 2.53 | 992.6 | 2322.57 | 2305321.77 | 1722721.77 | 2.957 |
| 15 | 29129 | 873870.0 | True | 0.3937 | 11468.7 | 10.0 | 4.37 | 1146.9 | 1744.97 | 2001245.31 | 1127375.31 | 1.2901 |
| 20 | 38839 | 1165170.0 | False | 0.3274 | 12716.7 | 10.0 | 6.17 | 1271.7 | 1484.84 | 1888222.21 | 723052.21 | 0.6206 |
| 25 | 48548 | 1456440.0 | False | 0.2785 | 13522.0 | 10.0 | 7.98 | 1352.2 | 1349.97 | 1825421.54 | 368981.54 | 0.2533 |
| 30 | 58258 | 1747740.0 | False | 0.243 | 14158.7 | 10.0 | 9.73 | 1415.9 | 1269.06 | 1796820.66 | 49080.66 | 0.0281 |

## Recommended scenario under the configured budget

| capacity_percent | customers_targeted | campaign_spend | within_budget | average_calibrated_risk | expected_churners | assumed_save_rate_percent | break_even_save_rate_percent | expected_saved_customers | value_per_saved_customer | scenario_retained_value | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 9710 | 291300.0 | True | 0.7253 | 7042.7 | 10.0 | 1.13 | 704.3 | 3646.15 | 2567888.22 | 2276588.22 | 7.8153 |

The recommended option is the capacity grid row with the highest scenario net value while remaining within the configured budget.