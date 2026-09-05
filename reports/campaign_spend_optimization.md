# Campaign Spend Optimization

## Interpretation boundary

This analysis uses model-estimated churn risk plus editable business assumptions. It is not realized campaign profit. Validate the selected offer and audience through an experiment before operational rollout.

Monetary unit label: **dataset currency units**. Value proxy multiplier: **1.0**.

Maximum campaign budget: **1,000,000.00 dataset currency units**.

## Capacity options

| capacity_percent | customers_targeted | campaign_spend | within_budget | average_calibrated_risk | expected_churners | assumed_save_rate_percent | break_even_save_rate_percent | expected_saved_customers | value_per_saved_customer | scenario_retained_value | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 1942 | 58260.0 | True | 0.935699999332428 | 1817.0999755859375 | 10.0 | 0.73 | 181.6999969482422 | 4379.02 | 795694.02 | 737434.02 | 12.6576 |
| 2 | 3884 | 116520.0 | True | 0.8998000025749207 | 3494.800048828125 | 10.0 | 0.62 | 349.5 | 5390.04 | 1883720.71 | 1767200.71 | 15.1665 |
| 5 | 9710 | 291300.0 | True | 0.7146000266075134 | 6939.2001953125 | 10.0 | 1.11 | 693.9000244140625 | 3768.77 | 2615214.39 | 2323914.39 | 7.9777 |
| 10 | 19420 | 582600.0 | True | 0.5110999941825867 | 9924.900390625 | 10.0 | 2.51 | 992.5 | 2334.28 | 2316750.45 | 1734150.45 | 2.9766 |
| 15 | 29129 | 873870.0 | True | 0.3939000070095062 | 11474.099609375 | 10.0 | 4.34 | 1147.4000244140625 | 1756.76 | 2015732.85 | 1141862.85 | 1.3067 |
| 20 | 38839 | 1165170.0 | False | 0.32749998569488525 | 12720.7001953125 | 10.0 | 6.15 | 1272.0999755859375 | 1488.33 | 1893258.51 | 728088.51 | 0.6249 |
| 25 | 48548 | 1456440.0 | False | 0.2784999907016754 | 13522.0 | 10.0 | 7.98 | 1352.199951171875 | 1350.54 | 1826197.8 | 369757.8 | 0.2539 |
| 30 | 58258 | 1747740.0 | False | 0.24330000579357147 | 14173.7998046875 | 10.0 | 9.75 | 1417.4000244140625 | 1265.23 | 1793310.83 | 45570.83 | 0.0261 |

## Recommended scenario under the configured budget

| capacity_percent | customers_targeted | campaign_spend | within_budget | average_calibrated_risk | expected_churners | assumed_save_rate_percent | break_even_save_rate_percent | expected_saved_customers | value_per_saved_customer | scenario_retained_value | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 9710 | 291300.0 | True | 0.7146 | 6939.2 | 10.0 | 1.11 | 693.9 | 3768.77 | 2615214.39 | 2323914.39 | 7.9777 |

The recommended option is the capacity grid row with the highest scenario net value while remaining within the configured budget.