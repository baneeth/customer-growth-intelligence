# Business Brief — Version 0.1

## Company context

This case study uses anonymized data released by KKBox, a real digital music
subscription service. It is an independent educational analysis and must not be
presented as work commissioned by, deployed at, or endorsed by KKBox.

## Decision to support

Before a subscriber reaches the end of a paid subscription period, the growth
team must decide whether the subscriber should enter a retention campaign.
Campaign capacity and discount budgets are limited, so ranking customers is more
useful than generating an isolated churn probability.

## Prediction unit

One row represents one subscriber at one decision snapshot.

## Initial target

A subscriber is treated as churned when they do not renew within 30 days after
their current subscription expires. The exact implementation will be verified
against the official dataset documentation before labels are reconstructed.

## Observation and outcome windows

- Observation window: subscriber information available on or before the
  snapshot date.
- Outcome window: the 30 days following subscription expiration.
- No feature may contain information recorded after the snapshot date.

## Primary users

- Growth leader: revenue at risk and campaign return
- CRM manager: prioritized campaign audience
- Product manager: engagement patterns associated with churn
- Finance partner: modeled value, cost, and scenario assumptions
- Data team: pipeline quality, model behavior, and monitoring

## Success criteria

### Analytical

- Reliable out-of-time probability estimates
- Strong lift among the limited population the team can contact
- Well-calibrated risk scores
- Stable performance across important customer segments

### Business

- More expected retained value than random targeting
- More expected retained value than churn-risk-only targeting
- Recommendations that respect campaign capacity and assumed costs

### Engineering

- Repeatable ingestion and transformation
- Immutable raw data and traceable source manifests
- Automated schema, quality, and leakage tests
- Reproducible training and scoring

## Known limitations

- Customer identities are anonymized.
- The data does not represent full company accounting.
- True customer-level profit and acquisition cost are unavailable.
- Historical randomized retention treatments are unavailable.
- Any treatment-effect demonstration must therefore be explicitly simulated
  until genuine experimental data exists.

## Questions to revisit after data profiling

1. Which date should serve as the operational prediction snapshot?
2. How complete is activity-log coverage for labeled subscribers?
3. How should transaction reversals and same-day corrections be ordered?
4. Which payment fields can defensibly support a value proxy?
5. Which customer attributes are too incomplete or unreliable for modeling?

