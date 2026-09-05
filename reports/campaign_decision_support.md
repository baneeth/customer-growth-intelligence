# Retention Campaign Decision Support

## Important interpretation

This is a scenario model, not an observed campaign result. Offer cost, save rate, and value months are explicit assumptions in `configs/campaign_scenario.json`. Model scores estimate churn risk; they do not prove an offer will save every targeted customer.

## Main scenario

| campaign_capacity_percent | assumed_save_rate_percent | customers_targeted | average_calibrated_risk | expected_churners_from_model | average_monthly_value_proxy | offer_cost_per_customer | value_months | expected_saved_customers | scenario_retained_value | campaign_cost | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 10 | 10.0 | 19420 | 0.5110999941825867 | 9924.900390625 | 389.07 | 30.0 | 6 | 992.5 | 2316868.2 | 582600.0 | 1734268.2 | 2.9768 |

## Sensitivity analysis

| campaign_capacity_percent | assumed_save_rate_percent | customers_targeted | average_calibrated_risk | expected_churners_from_model | average_monthly_value_proxy | offer_cost_per_customer | value_months | expected_saved_customers | scenario_retained_value | campaign_cost | scenario_net_value | scenario_roi |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | 5.0 | 9710 | 0.7146000266075134 | 6939.2001953125 | 628.11 | 30.0 | 6 | 347.0 | 1307573.32 | 291300.0 | 1016273.32 | 3.4888 |
| 5 | 10.0 | 9710 | 0.7146000266075134 | 6939.2001953125 | 628.11 | 30.0 | 6 | 693.9000244140625 | 2615146.64 | 291300.0 | 2323846.64 | 7.9775 |
| 5 | 20.0 | 9710 | 0.7146000266075134 | 6939.2001953125 | 628.11 | 30.0 | 6 | 1387.800048828125 | 5230293.29 | 291300.0 | 4938993.29 | 16.955 |
| 10 | 5.0 | 19420 | 0.5110999941825867 | 9924.900390625 | 389.07 | 30.0 | 6 | 496.20001220703125 | 1158434.1 | 582600.0 | 575834.1 | 0.9884 |
| 10 | 10.0 | 19420 | 0.5110999941825867 | 9924.900390625 | 389.07 | 30.0 | 6 | 992.5 | 2316868.2 | 582600.0 | 1734268.2 | 2.9768 |
| 10 | 20.0 | 19420 | 0.5110999941825867 | 9924.900390625 | 389.07 | 30.0 | 6 | 1985.0 | 4633736.41 | 582600.0 | 4051136.41 | 6.9535 |
| 20 | 5.0 | 38839 | 0.32749998569488525 | 12720.7001953125 | 248.03 | 30.0 | 6 | 636.0 | 946547.11 | 1165170.0 | -218622.89 | -0.1876 |
| 20 | 10.0 | 38839 | 0.32749998569488525 | 12720.7001953125 | 248.03 | 30.0 | 6 | 1272.0999755859375 | 1893094.22 | 1165170.0 | 727924.22 | 0.6247 |
| 20 | 20.0 | 38839 | 0.32749998569488525 | 12720.7001953125 | 248.03 | 30.0 | 6 | 2544.10009765625 | 3786188.44 | 1165170.0 | 2621018.44 | 2.2495 |

## Operational use

The deployable priority list contains the highest-risk 10% of test customers (19,420 rows). It excludes the later churn label, because that label is unavailable when a real campaign is sent.