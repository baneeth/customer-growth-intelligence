# XGBoost and Probability Calibration

XGBoost trained on 200,000 customers, calibrated on a separate 100,000 customers, and evaluated on 194,192 unseen customers.

## Performance

| model | test_customers | roc_auc | average_precision | brier_score | top_10_percent_actual_churn | lift_at_top_10_percent |
|---|---|---|---|---|---|---|
| xgboost_raw | 194192 | 0.870034 | 0.575945 | 0.128182 | 0.505973 | 5.625555 |
| xgboost_isotonic_calibrated | 194192 | 0.869868 | 0.567243 | 0.05449 | 0.506179 | 5.627846 |

## Calibration check

| risk_band | customers | average_predicted_risk | actual_churn_rate |
|---|---|---|---|
| (-0.001, 0.1] | 155687 | 0.029963815584778786 | 0.03002819760159808 |
| (0.1, 0.2] | 17572 | 0.13903988897800446 | 0.14984065558843615 |
| (0.2, 0.3] | 5902 | 0.23761838674545288 | 0.22958319213825823 |
| (0.3, 0.4] | 4502 | 0.34075742959976196 | 0.32407818747223455 |
| (0.4, 0.5] | 3771 | 0.47429269552230835 | 0.47706178732431714 |
| (0.5, 0.6] | 58 | 0.5717122554779053 | 0.5172413793103449 |
| (0.6, 0.7] | 1456 | 0.6429776549339294 | 0.6620879120879121 |
| (0.7, 0.8] | 1027 | 0.7534246444702148 | 0.7653359298928919 |
| (0.8, 0.9] | 2766 | 0.865982711315155 | 0.8698481561822126 |
| (0.9, 1.0] | 1451 | 0.9515364766120911 | 0.9365954514128187 |

## Capacity-based campaign threshold

| campaign_capacity | calibrated_risk_threshold | customers_targeted | actual_churn_rate_in_targeted_group | overall_test_churn_rate |
|---|---|---|---|---|
| top 10 percent of customers by calibrated risk | 0.21148036420345306 | 19420 | 0.5061791967044285 | 0.08994191315811156 |

## Most influential XGBoost inputs

| feature | importance |
|---|---|
| numeric__amount_paid_last_31_days | 0.2919379770755768 |
| numeric__latest_is_auto_renew | 0.2441362887620926 |
| numeric__transaction_count_last_31_days | 0.1823900192975998 |
| numeric__auto_renew_rate | 0.03760729357600212 |
| numeric__days_since_last_transaction | 0.02915232628583908 |
| numeric__latest_amount_paid | 0.023113053292036057 |
| numeric__total_discount_amount | 0.016775410622358322 |
| numeric__days_since_first_transaction | 0.013770162127912045 |
| numeric__total_amount_paid | 0.013267985545098782 |
| numeric__latest_list_price | 0.012424865737557411 |
| numeric__transaction_count_last_90_days | 0.010444486513733864 |
| numeric__transaction_count_to_cutoff | 0.010000193491578102 |
| numeric__has_member_profile_flag | 0.008884241804480553 |
| numeric__discount_rate | 0.00848366692662239 |
| numeric__total_list_price | 0.008374709635972977 |
| category__latest_payment_method_category | 0.008242230862379074 |
| category__registration_channel_category | 0.007840627804398537 |
| numeric__cancellations_last_31_days | 0.0073374174535274506 |
| numeric__latest_is_cancel | 0.006659537088125944 |
| numeric__average_amount_paid | 0.0062652090564370155 |