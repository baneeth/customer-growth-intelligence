# Baseline Churn Models

Both models trained on the same stratified sample of 200,000 customers and were evaluated on 194,192 unseen customers.

## Model metrics

| model | test_customers | base_churn_rate | roc_auc | average_precision | precision_at_0_50 | recall_at_0_50 | accuracy_at_0_50 | top_10_percent_churn_rate | lift_at_top_10_percent |
|---|---|---|---|---|---|---|---|---|---|
| logistic_regression | 194192 | 0.089942 | 0.824004 | 0.472059 | 0.339995 | 0.661342 | 0.854072 | 0.463337 | 5.151511 |
| random_forest | 194192 | 0.089942 | 0.861937 | 0.546822 | 0.351086 | 0.682011 | 0.858022 | 0.496344 | 5.518495 |

## Random Forest: most influential features

| feature | importance |
|---|---|
| numeric__amount_paid_last_31_days | 0.13017960689537833 |
| numeric__transaction_count_last_31_days | 0.10326045682560261 |
| numeric__latest_is_auto_renew | 0.09835138930968305 |
| numeric__days_since_last_transaction | 0.09759081729852728 |
| numeric__transaction_count_last_90_days | 0.07758194575399117 |
| numeric__auto_renew_rate | 0.05822412091603591 |
| numeric__latest_amount_paid | 0.04532195496942504 |
| category__latest_payment_method_category_41 | 0.0379592651479924 |
| numeric__transaction_count_to_cutoff | 0.033586760852014085 |
| numeric__total_amount_paid | 0.02810967117693231 |
| numeric__average_amount_paid | 0.025782396702158976 |
| category__latest_plan_days_category_30 | 0.025770141713213623 |
| numeric__days_since_first_transaction | 0.02303828775008403 |
| category__latest_payment_method_category_38 | 0.022602981282265053 |
| numeric__total_list_price | 0.021962894551244935 |
| numeric__latest_list_price | 0.020946926839669106 |
| category__registration_channel_category_7 | 0.01854901504281939 |
| numeric__days_since_registration | 0.012100804946822767 |
| numeric__discount_rate | 0.01032844134512723 |
| numeric__total_discount_amount | 0.009711998093699856 |

Metrics are descriptive first-pass results. Calibration and threshold selection are separate next steps.