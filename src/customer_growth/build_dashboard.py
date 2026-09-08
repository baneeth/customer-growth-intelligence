from __future__ import annotations

from html import escape
from pathlib import Path
import json

import pandas as pd


PROJECT_ROOT = Path(r"C:\Users\banee\Documents\Codex\2026-08-03\b\outputs\customer-growth-intelligence")
REPORTS = PROJECT_ROOT / "reports"
CONFIG = PROJECT_ROOT / "configs" / "campaign_scenario.json"
OUTPUT = REPORTS / "executive_dashboard.html"
PUBLIC_DASHBOARD = PROJECT_ROOT / "public" / "index.html"


def money(value: float, label: str) -> str:
    return f"{value:,.0f} {escape(label)}"


def number(value: float, digits: int = 0) -> str:
    return f"{value:,.{digits}f}"


def first_matching_row(frame: pd.DataFrame, text: str) -> pd.Series:
    mask = frame.astype(str).apply(lambda column: column.str.contains(text, case=False, na=False)).any(axis=1)
    return frame.loc[mask].iloc[0] if mask.any() else frame.iloc[-1]


def horizontal_bar_chart(title: str, rows: list[tuple[str, float]], suffix: str, color: str) -> str:
    height = 58 * len(rows) + 55
    bars = []
    for index, (label, value) in enumerate(rows):
        y = 42 + index * 58
        width = value / 100 * 430
        bars.append(
            f"<text x='0' y='{y + 17}' class='chart-label'>{escape(label)}</text>"
            f"<rect x='170' y='{y}' width='430' height='24' rx='4' class='chart-track'/>"
            f"<rect x='170' y='{y}' width='{width:.1f}' height='24' rx='4' fill='{color}'/>"
            f"<text x='{min(610, 178 + width):.1f}' y='{y + 17}' class='chart-value'>{value:.2f}{suffix}</text>"
        )
    return f"""<svg viewBox='0 0 660 {height}' role='img' aria-label='{escape(title)}'>
      <title>{escape(title)}</title><text x='0' y='20' class='chart-title'>{escape(title)}</text>{''.join(bars)}</svg>"""


def comparison_column_chart(title: str, rows: list[tuple[str, float]]) -> str:
    maximum, base_y, top_y = max(value for _, value in rows) * 1.15, 245, 60
    start_x, bar_width, gap = 105, 110, 125
    bars = []
    for index, (label, value) in enumerate(rows):
        height = value / maximum * (base_y - top_y)
        x, y = start_x + index * (bar_width + gap), base_y - height
        bars.append(
            f"<rect x='{x}' y='{y:.1f}' width='{bar_width}' height='{height:.1f}' rx='5' fill='#2474c6'/>"
            f"<text x='{x + bar_width / 2:.1f}' y='{y - 9:.1f}' text-anchor='middle' class='chart-value'>{value:.2f}%</text>"
            f"<text x='{x + bar_width / 2:.1f}' y='{base_y + 23}' text-anchor='middle' class='chart-label'>{escape(label)}</text>"
        )
    return f"""<svg viewBox='0 0 580 295' role='img' aria-label='{escape(title)}'>
      <title>{escape(title)}</title><text x='0' y='20' class='chart-title'>{escape(title)}</text>
      <line x1='55' y1='{base_y}' x2='530' y2='{base_y}' class='chart-axis'/>{''.join(bars)}
      <text x='292' y='288' text-anchor='middle' class='chart-subtitle'>Customer group</text></svg>"""


def model_lollipop_chart(rows: list[tuple[str, float, float, float]]) -> str:
    min_value, max_value, axis_x = 0.80, 0.88, 125
    y_start, y_gap, width = 75, 60, 630
    marks = []
    for index, (label, auc, _, _) in enumerate(rows):
        y = y_start + index * y_gap
        x = axis_x + (auc - min_value) / (max_value - min_value) * 430
        marks.append(
            f"<text x='0' y='{y + 4}' class='chart-label'>{escape(label)}</text>"
            f"<line x1='{axis_x}' y1='{y}' x2='{x:.1f}' y2='{y}' class='lollipop-line'/>"
            f"<circle cx='{x:.1f}' cy='{y}' r='8' fill='#0b7a53'/>"
            f"<text x='{x + 14:.1f}' y='{y + 4}' class='chart-value'>{auc:.3f}</text>"
        )
    ticks = "".join(
        f"<text x='{axis_x + (tick-min_value)/(max_value-min_value)*430:.1f}' y='266' text-anchor='middle' class='chart-label'>{tick:.2f}</text>"
        for tick in [0.80, 0.82, 0.84, 0.86, 0.88]
    )
    return f"""<svg viewBox='0 0 {width} 285' role='img' aria-label='How well each approach ranks customer risk'>
      <title>How well each approach ranks customer risk</title><text x='0' y='20' class='chart-title'>How well each approach ranks customer risk</text>
      <line x1='{axis_x}' y1='235' x2='555' y2='235' class='chart-axis'/>{marks}{ticks}
      <text x='340' y='283' text-anchor='middle' class='chart-subtitle'>AUC score: higher means better ordering of customer risk</text></svg>"""


def campaign_chart(frame: pd.DataFrame, currency: str) -> str:
    values = frame["scenario_net_value"].astype(float).tolist()
    maximum = max(values) if values else 1
    width, height, base_y, top_y = 680, 310, 250, 72
    gap, start_x = 75, 54
    points, marks = [], []
    for index, row in enumerate(frame.itertuples(index=False)):
        value = float(row.scenario_net_value)
        x, y = start_x + index * gap, base_y - value / maximum * (base_y - top_y)
        fill = "#0b7a53" if bool(row.within_budget) else "#94a3b8"
        label = f"{value / 1_000_000:.2f}M"
        points.append(f"{x},{y:.1f}")
        marks.append(
            f"<circle cx='{x}' cy='{y:.1f}' r='6' fill='{fill}'/>"
            f"<text x='{x}' y='{y - 11:.1f}' text-anchor='middle' class='chart-value'>{label}</text>"
            f"<text x='{x}' y='{base_y + 22}' text-anchor='middle' class='chart-label'>{row.capacity_percent:g}%</text>"
        )
    return f"""<svg viewBox='0 0 {width} {height}' role='img' aria-label='Estimated value by campaign size'>
      <title>Estimated value by campaign size</title>
      <text x='0' y='20' class='chart-title'>Estimated value by campaign size</text>
      <text x='0' y='43' class='chart-subtitle'>Green options fit the budget. Gray options cost more than the budget. Values are planning estimates.</text>
      <line x1='35' y1='{base_y}' x2='660' y2='{base_y}' class='chart-axis'/><polyline points='{' '.join(points)}' class='campaign-line'/>{''.join(marks)}
      <text x='347' y='294' text-anchor='middle' class='chart-subtitle'>Campaign capacity</text></svg>"""


def risk_driver_chart(title: str, frame: pd.DataFrame, category_column: str) -> str:
    friendly_labels = {
        "0": "Auto-renewal is off",
        "1": "Auto-renewal is on",
        "no_history": "No recent payment record",
        "no safe payment history": "No recent payment record",
    }
    rows = list(frame[[category_column, "churn_percent"]].itertuples(index=False, name=None))
    height, label_x, bar_x, bar_width = 58 * len(rows) + 60, 0, 270, 390
    bars = []
    for index, (label, value) in enumerate(rows):
        display_label = friendly_labels.get(str(label), str(label))
        y = 42 + index * 58
        width = float(value) / 100 * bar_width
        bars.append(
            f"<text x='{label_x}' y='{y + 17}' class='chart-label'>{escape(display_label)}</text>"
            f"<rect x='{bar_x}' y='{y}' width='{bar_width}' height='24' rx='4' class='chart-track'/>"
            f"<rect x='{bar_x}' y='{y}' width='{width:.1f}' height='24' rx='4' fill='#2474c6'/>"
            f"<text x='{min(bar_x + bar_width - 28, bar_x + width + 8):.1f}' y='{y + 17}' class='chart-value'>{float(value):.2f}%</text>"
        )
    return f"""<svg viewBox='0 0 710 {height}' role='img' aria-label='{escape(title)}'>
      <title>{escape(title)}</title><text x='0' y='20' class='chart-title'>{escape(title)}</text>{''.join(bars)}</svg>"""


def main() -> None:
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    currency = str(config["monetary_unit_label"])
    tournament = pd.read_csv(REPORTS / "model_tournament_metrics.csv")
    winner = json.loads((REPORTS / "model_tournament_winner.json").read_text(encoding="utf-8"))
    spend_options = pd.read_csv(REPORTS / "campaign_spend_optimization.csv")
    recommendation = pd.read_csv(REPORTS / "campaign_spend_recommendation.csv").iloc[0]
    auto_renewal = pd.read_csv(REPORTS / "tables" / "churn_by_latest_auto_renewal.csv")
    payment_recency = pd.read_csv(REPORTS / "tables" / "churn_by_payment_recency.csv")
    transaction_frequency = pd.read_csv(REPORTS / "tables" / "churn_by_transaction_frequency.csv")

    friendly_names = {
        "xgboost_isotonic_calibrated": "Calibrated XGBoost",
        "catboost_isotonic_calibrated": "Calibrated CatBoost",
        "lightgbm_isotonic_calibrated": "Calibrated LightGBM",
    }
    # Accuracy uses a 50% risk cutoff. The campaign itself ranks customers and
    # contacts the highest-risk group, so top-10% lift is the lead decision metric.
    model_rows = [
        (
            friendly_names[str(row.model)],
            float(row.roc_auc),
            float(row.lift_at_top_10_percent),
            float(row.accuracy_at_50_percent_risk),
        )
        for row in tournament.itertuples(index=False)
    ]
    selected = tournament.loc[tournament["model"] == winner["selected_model"]].iloc[0]
    selected_name = friendly_names[str(selected["model"])]
    churn_chart = comparison_column_chart(
        "The top of the contact list contains far more churn",
        [("All customers", 8.99), ("Highest-risk 10%", float(selected["top_10_percent_actual_churn"]) * 100)],
    )
    model_chart = model_lollipop_chart(model_rows)
    campaign_net_chart = campaign_chart(spend_options, currency)
    auto_renewal_chart = risk_driver_chart("Customers with auto-renewal off are much more likely to leave", auto_renewal, "latest_auto_renewal")
    recency_chart = risk_driver_chart("Time since last payment: a strong early warning sign", payment_recency, "recency_segment")
    frequency_chart = risk_driver_chart("Longer payment history is linked with lower churn", transaction_frequency, "payment_frequency_segment")

    model_html = "".join(
        f"""<tr><td>{name}</td><td>{accuracy * 100:.1f}%</td><td>{auc:.3f}</td><td>{lift:.2f}x</td></tr>"""
        for name, auc, lift, accuracy in model_rows
    )
    spend_html = "".join(
        f"""<tr class='{ 'recommended' if float(row.capacity_percent) == float(recommendation.capacity_percent) else '' }'>
        <td>{number(row.capacity_percent)}%</td><td>{number(row.customers_targeted):s}</td>
        <td>{money(float(row.campaign_spend), currency)}</td>
        <td>{number(float(row.average_calibrated_risk) * 100, 1)}%</td>
        <td>{number(float(row.break_even_save_rate_percent), 2)}%</td>
        <td>{money(float(row.scenario_net_value), currency)}</td>
        <td>{'Yes' if bool(row.within_budget) else 'No'}</td></tr>"""
        for row in spend_options.itertuples(index=False)
    )

    output = f"""<!doctype html>
<html lang='en'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Customer Growth Decision Intelligence</title>
  <style>
    :root {{ --ink:#142033; --muted:#5e6c84; --navy:#12355b; --blue:#2474c6; --blue-soft:#eaf3ff; --green:#0b7a53; --green-soft:#e8f7f0; --line:#dce4ee; --paper:#f6f8fb; --white:#fff; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.5 Arial,sans-serif; }}
    main {{ max-width:1120px; margin:auto; padding:42px 24px 60px; }}
    header {{ min-height:270px; display:flex; align-items:flex-end; background-image:linear-gradient(90deg,rgba(10,35,67,.90) 0%,rgba(10,35,67,.72) 48%,rgba(10,35,67,.30) 100%),url('assets/retention-hero.png'); background-position:center; background-size:cover; color:white; border-radius:16px; padding:34px; }}
    .hero-copy {{ max-width:620px; }} .byline {{ margin:15px 0 0; font-size:13px; font-weight:700; letter-spacing:.04em; opacity:.92; text-transform:uppercase; }}
    h1 {{ margin:0 0 8px; font-size:30px; }} h2 {{ font-size:21px; margin:0 0 12px; }} h3 {{ font-size:15px; margin:0 0 7px; }}
    .subtitle {{ margin:0; opacity:.9; max-width:720px; }} .grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin:20px 0; }}
    .card {{ background:var(--white); border:1px solid var(--line); border-radius:12px; padding:17px; }} .label {{ color:var(--muted); font-size:12px; }} .value {{ font-size:24px; font-weight:700; margin:4px 0; }}
    .small {{ color:var(--muted); font-size:12px; }} section {{ margin-top:22px; }} .two {{ display:grid; grid-template-columns:1.1fr .9fr; gap:20px; }}
    table {{ border-collapse:collapse; width:100%; background:var(--white); border:1px solid var(--line); border-radius:12px; overflow:hidden; }} th,td {{ padding:11px 12px; text-align:left; border-bottom:1px solid var(--line); white-space:nowrap; }} th {{ font-size:12px; color:var(--muted); background:#fbfcfe; }} tr:last-child td {{ border-bottom:0; }} .recommended {{ background:var(--green-soft); font-weight:700; }}
    .bar-track {{ height:8px; background:#e7edf4; border-radius:8px; width:120px; }} .bar {{ height:100%; background:var(--blue); border-radius:8px; }}
    .callout {{ background:var(--blue-soft); border-left:4px solid var(--blue); padding:16px; border-radius:6px; }} .green {{ background:var(--green-soft); border-left-color:var(--green); }}
    .chart {{ background:var(--white); border:1px solid var(--line); border-radius:12px; padding:16px; }} .chart svg {{ display:block; width:100%; height:auto; }} .chart-title {{ fill:var(--ink); font-size:16px; font-weight:700; }} .chart-subtitle,.chart-label {{ fill:var(--muted); font-size:12px; }} .chart-value {{ fill:var(--ink); font-size:12px; font-weight:700; }} .chart-track {{ fill:#e7edf4; }} .chart-axis {{ stroke:var(--line); stroke-width:1; }} .lollipop-line {{ stroke:#a5b4c5; stroke-width:3; }} .campaign-line {{ fill:none; stroke:#2474c6; stroke-width:3; }} .driver-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; }} .driver-grid .chart:last-child {{ grid-column:1 / -1; }}
    .scroll {{ overflow:auto; }} code {{ background:#edf1f6; padding:2px 5px; border-radius:4px; }}
    @media(max-width:800px) {{ .grid {{ grid-template-columns:repeat(2,1fr); }} .two,.driver-grid {{ grid-template-columns:1fr; }} .driver-grid .chart:last-child {{ grid-column:auto; }} }} @media(max-width:460px) {{ main {{ padding:18px 12px; }} header {{ padding:24px; }} .grid {{ grid-template-columns:1fr; }} h1 {{ font-size:25px; }} }}
  </style>
</head>
<body><main>
  <header><div class='hero-copy'><h1>Customer Growth Decision Intelligence</h1><p class='subtitle'>A practical guide for deciding who needs retention support first, how large the outreach should be, and what the plan could be worth.</p><p class='byline'>Project made by Baneeth S. Bandi</p></div></header>
  <div class='grid'>
    <div class='card'><div class='label'>Customers reviewed</div><div class='value'>970,960</div><div class='small'>One customer record per row</div></div>
    <div class='card'><div class='label'>Customers who left</div><div class='value'>8.99%</div><div class='small'>About 9 in every 100 customers</div></div>
    <div class='card'><div class='label'>Accuracy at a 50% risk cutoff</div><div class='value'>{number(float(selected['accuracy_at_50_percent_risk']) * 100, 1)}%</div><div class='small'>{selected_name}, selected after a fair model tournament</div></div>
    <div class='card'><div class='label'>Churn in the highest-risk 10%</div><div class='value'>{number(float(selected['top_10_percent_actual_churn']) * 100, 2)}%</div><div class='small'>About 51 in every 100 customers</div></div>
  </div>
  <section class='two'><div class='card'><h2>What this helps a team do</h2><p>The model puts customers in order from most likely to leave to least likely. A retention team can then spend its time on the people where help is most likely to matter.</p><div class='callout'><strong>One clear warning sign:</strong> customers with auto-renewal switched off left far more often than customers with it on: 38.70% compared with 4.67%. This is a useful signal, not proof that switching it off causes someone to leave.</div></div>
  <div class='card'><h2>A fair prediction rule</h2><p>We only used information the company would have known by <strong>January 31, 2017</strong>.</p><p class='small'>What happened in February and March was kept aside as the answer sheet. That makes this an honest test of whether the approach could help before customers leave.</p></div></section>
  <section><h2>How well did the approach work?</h2><p class='small'>We ran a fair tournament between XGBoost, CatBoost, and LightGBM using the same unseen customers. <strong>{selected_name}</strong> was selected because it found the most churn among the highest-risk 10% while also giving the most reliable risk estimates. Accuracy means how often a simple yes/no decision is correct at a 50% risk line; because most customers stayed, it is helpful but not the main decision measure.</p><div class='scroll'><table><thead><tr><th>Approach</th><th>Accuracy at 50% risk</th><th>Ability to rank risk (AUC)</th><th>Churn concentration in highest-risk 10%</th></tr></thead><tbody>{model_html}</tbody></table></div></section>
  <section class='two'><div class='chart'>{churn_chart}</div><div class='chart'>{model_chart}</div></section>
  <section><h2>What we learned about customers</h2><p class='small'>These are patterns in past customer behaviour. They point the team toward useful conversations, but they do not prove that any one action caused a customer to leave.</p><div class='driver-grid'><div class='chart'>{auto_renewal_chart}</div><div class='chart'>{frequency_chart}</div><div class='chart'>{recency_chart}</div></div></section>
  <section><div class='callout green'><h2>Campaign recommendation: start with 9,710 customers</h2><p><strong>Why this group?</strong> Contacting the highest-risk 5% gives the largest estimated total value while staying within the current budget. Their average predicted risk of leaving is {number(float(recommendation.average_calibrated_risk)*100,1)}%, so this is a focused list rather than a message sent to everyone.</p><p><strong>What it costs:</strong> {money(float(recommendation.campaign_spend), currency)} at {money(float(config['offer_cost_per_customer']), currency)} per customer contacted. The scenario assumes that 10% of the people who would otherwise leave are persuaded to stay: roughly {number(float(recommendation.expected_saved_customers)):s} customers.</p><p><strong>What success is needed:</strong> the campaign only needs to keep about {number(float(recommendation.break_even_save_rate_percent),2)}% of the customers expected to leave for its estimated retained value to cover the outreach cost. The {money(float(recommendation.scenario_net_value), currency)} figure is a planning estimate, not money already earned.</p></div></section>
  <section><h2>Why not contact everyone?</h2><p class='small'>As the contact list grows, it includes more people who are less likely to leave. The team spends more, while each additional message is less likely to prevent churn. A 1% or 2% campaign is more efficient per unit spent, but the 5% option creates the highest estimated total value within the available budget.</p><div class='scroll'><table><thead><tr><th>Share of customers to contact</th><th>People contacted</th><th>Campaign cost</th><th>Average chance of leaving</th><th>Minimum save rate needed</th><th>Estimated net value</th><th>Fits current budget?</th></tr></thead><tbody>{spend_html}</tbody></table></div></section>
  <section class='chart'>{campaign_net_chart}</section>
  <section class='two'><div class='card'><h2>What a manager can change</h2><p>Before launching, the team can update:</p><ul><li>The cost of the offer or contact</li><li>How often an offer is expected to keep someone</li><li>How long a retained customer is expected to stay</li><li>The budget and number of people the team can handle</li></ul><p class='small'>Changing these assumptions updates the recommendation; it does not change the underlying customer-risk ranking.</p></div><div class='card'><h2>What happens next in a real company</h2><p>Run a small test. Contact one selected group and keep a similar group as a comparison. Then measure whether the offer truly reduces churn before spending more widely.</p><p class='small'>Subscription payments in this project are a stand-in for customer value, not confirmed profit or lifetime value.</p></div></section>
</main></body></html>"""
    OUTPUT.write_text(output, encoding="utf-8")
    PUBLIC_DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    PUBLIC_DASHBOARD.write_text(output, encoding="utf-8")
    print(OUTPUT)
    print(PUBLIC_DASHBOARD)


if __name__ == "__main__":
    main()
