# Retention Analytics: January 31 Customer Snapshot

These descriptive results use only the leakage-safe customer snapshot. They show association, not proof that one customer behaviour causes another.

## Churn By Latest Auto Renewal

| latest_auto_renewal | customers | churn_percent |
|---|---|---|
| 0 | 108382 | 38.7 |
| no_history | 33143 | 20.14 |
| 1 | 829435 | 4.67 |

## Churn By Payment Recency

| recency_segment | customers | churn_percent |
|---|---|---|
| over 90 days since payment | 33006 | 71.6 |
| 31-90 days since payment | 22714 | 52.69 |
| no safe payment history | 33143 | 20.14 |
| 8-30 days since payment | 585476 | 5.62 |
| 0-7 days since payment | 296621 | 4.11 |

## Churn By Transaction Frequency

| payment_frequency_segment | customers | churn_percent |
|---|---|---|
| 1-3 payments | 96174 | 22.45 |
| no safe payment history | 33143 | 20.14 |
| 4-10 payments | 204576 | 9.5 |
| 11-25 payments | 554015 | 6.37 |
| 26+ payments | 83052 | 5.21 |

## Churn By Profile Availability

| has_transaction_history_flag | has_member_profile_flag | customers | churn_percent |
|---|---|---|---|
| 0 | 1 | 10084 | 32.29 |
| 0 | 0 | 23059 | 14.83 |
| 1 | 1 | 832731 | 9.12 |
| 1 | 0 | 105086 | 4.51 |
