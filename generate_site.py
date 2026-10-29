import json

LABELS = {
    "cpi": ("CPI inflation", "Macro & Fiscal"),
    "gdp_growth": ("GDP growth", "Macro & Fiscal"),
    "public_debt": ("Public sector net debt", "Macro & Fiscal"),
    "bank_rate": ("Bank Rate", "Monetary & Markets"),
    "ftse_volatility": ("FTSE 100 volatility", "Monetary & Markets"),
    "gbp_fx_volatility": ("GBP FX volatility", "Monetary & Markets"),
    "unemployment": ("Unemployment rate", "Labour"),
    "job_security": ("Job Security Proxy", "Labour"),
    "composite_sentiment": ("Composite Sentiment", "Confidence"),
    "crime_rate": ("Crime rate", "Social & Wellbeing"),
    "purchasing_power": ("Real purchasing power", "Social & Wellbeing"),
    "wellbeing": ("Wellbeing (ONS4)", "Social & Wellbeing"),
}


def fmt_score(v: float) -> tuple:
    cls = "panic" if v > 0.05 else ("calm" if v < -0.05 else "")
    sign = "+" if v >= 0 else "\u2212"
    return f"{sign}{abs(v):.3f}", cls


def build_rows(scores: dict) -> str:
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    rows = []
    for key, val in ordered:
        label, pillar = LABELS.get(key, (key, ""))
        text, cls = fmt_score(val)
        rows.append(
            f'<tr><td>{label}<span class="pillar">{pillar}</span></td>'
            f'<td class="num {cls}">{text}</td></tr>'
        )
    return "\n          ".join(rows)


def main():
    with open("data/ukpi_output.json") as f:
        data = json.load(f)

    ukpi = data["ukpi"]
    ref_month = data["reference_month"]
    generated = data["generated_at"]
    ukpi_cls = "panic" if ukpi > 0.05 else ("calm" if ukpi < -0.05 else "")
    ukpi_text = f"{'+' if ukpi >= 0 else '−'}{abs(ukpi):.2f}"

    rows_html = build_rows(data["component_scores"])

    html = TEMPLATE.format(
        ukpi_value=ukpi_text,
        ukpi_class=ukpi_cls,
        ref_month=ref_month,
        generated_at=generated,
        rows=rows_html,
    )

    with open("index.html", "w") as f:
        f.write(html)

    print(f"index.html generated — UKPI {ukpi_text}, reference {ref_month}")


TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UK Panic Index</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: Arial, Helvetica, sans-serif;
    background: #fff;
    color: #333;
    font-size: 14px;
    line-height: 1.45;
  }}

  /* Top navigation bar – Trading Economics style */
  .navbar {{
    background: #1a1a1a;
    color: #fff;
    height: 42px;
    display: flex;
    align-items: center;
    padding: 0 16px;
    font-size: 13px;
  }}
  .navbar .brand {{
    font-weight: bold;
    letter-spacing: 0.3px;
    margin-right: 28px;
  }}
  .navbar a {{
    color: #ccc;
    text-decoration: none;
    margin-right: 18px;
  }}
  .navbar a:hover {{ color: #fff; }}

  /* Blue page header */
  .page-header {{
    background: #3b7dd8;
    color: #fff;
    padding: 14px 20px;
    font-size: 20px;
    font-weight: bold;
  }}

  .container {{
    max-width: 960px;
    margin: 0 auto;
    padding: 20px 16px 48px;
  }}

  /* Main reading block */
  .reading {{
    margin-bottom: 28px;
  }}
  .reading .value {{
    font-size: 42px;
    font-weight: bold;
    line-height: 1.1;
    margin-bottom: 6px;
  }}
  .reading .value.panic {{ color: #c0392b; }}
  .reading .value.calm  {{ color: #1e8449; }}
  .reading .caption {{
    color: #555;
    font-size: 13px;
    max-width: 520px;
  }}

  /* Section titles */
  h2 {{
    font-size: 16px;
    font-weight: bold;
    color: #222;
    margin: 28px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid #ddd;
  }}

  /* Tables – clean TE style */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
  }}
  th {{
    text-align: left;
    font-weight: normal;
    color: #666;
    font-size: 12px;
    padding: 8px 10px;
    border-bottom: 1px solid #ccc;
    background: #f7f7f7;
  }}
  td {{
    padding: 9px 10px;
    border-bottom: 1px solid #eee;
    font-size: 13px;
  }}
  tr:hover td {{ background: #f9f9f9; }}
  td.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
    font-weight: bold;
  }}
  td.num.panic {{ color: #c0392b; }}
  td.num.calm  {{ color: #1e8449; }}
  .pillar {{
    color: #888;
    font-size: 11px;
    margin-left: 6px;
  }}

  /* Methodology text */
  .method p {{
    color: #444;
    margin-bottom: 10px;
    max-width: 640px;
  }}
  .method ul {{
    color: #444;
    margin: 0 0 12px 18px;
  }}
  .method li {{ margin-bottom: 3px; }}
  .method strong {{ color: #222; }}

  .weights {{
    display: grid;
    grid-template-columns: 1fr auto;
    gap: 4px 32px;
    margin: 10px 0 14px;
    max-width: 520px;
    font-size: 13px;
  }}
  .weights span:nth-child(even) {{
    text-align: right;
    color: #555;
  }}

  /* Footer */
  footer {{
    margin-top: 36px;
    padding-top: 12px;
    border-top: 1px solid #ddd;
    font-size: 12px;
    color: #777;
  }}
  footer a {{ color: #3b7dd8; text-decoration: none; }}
  footer a:hover {{ text-decoration: underline; }}

  @media (max-width: 600px) {{
    .reading .value {{ font-size: 34px; }}
    th, td {{ padding: 8px 6px; }}
  }}
</style>
</head>
<body>

<div class="navbar">
  <span class="brand">UK PANIC INDEX</span>
  <a href="https://github.com/RaphaelMonti/United-Kingdom-Panic-Index" target="_blank" rel="noopener">Source</a>
</div>

<div class="page-header">
  UK Panic Index
</div>

<div class="container">

  <div class="reading">
    <div class="value {ukpi_class}">{ukpi_value}</div>
    <div class="caption">
      Reference month: <strong>{ref_month}</strong>.  
      A reading of 0 represents the long-run average across all 12 indicators.  
      Positive values indicate more panic than normal; negative values indicate a calmer-than-normal reading.  
      Each 25 points corresponds to roughly one standard deviation of historical variation.
    </div>
  </div>

  <h2>Component readings</h2>
  <table>
    <thead>
      <tr>
        <th>Indicator</th>
        <th style="text-align:right">Last</th>
      </tr>
    </thead>
    <tbody>
      {rows}
    </tbody>
  </table>

  <h2>Methodology</h2>
  <div class="method">

    <p>
      The UKPI is a composite index of UK economic stability and public confidence.
      It combines 12 public indicators into a single monthly reading. Higher values
      mean elevated stress relative to each series’ own recent history.
    </p>

    <p><strong>Pillars and weights</strong></p>
    <div class="weights">
      <span>Macro &amp; Fiscal (CPI, GDP growth, public debt)</span><span>20%</span>
      <span>Monetary &amp; Markets (Bank Rate, FTSE vol, GBP FX vol)</span><span>20%</span>
      <span>Labour (unemployment, Job Security Proxy)</span><span>15%</span>
      <span>Confidence &amp; Sentiment (GfK CCI, Lloyds Business Barometer, EPU)</span><span>25%</span>
      <span>Social &amp; Wellbeing (crime, real purchasing power, ONS4 wellbeing)</span><span>20%</span>
    </div>
    <p>If an indicator cannot be scored, its weight is redistributed across the remaining series.</p>

    <p><strong>Normalization.</strong>  
    Every series is converted to a trailing z-score against its own 5-year history
    (minimum 24 observations for most series, 16 for GDP growth). The observation
    being scored is excluded from the baseline. Series where a higher raw value is
    beneficial are inverted so that a higher final score always means more panic.</p>

    <p><strong>Frequency.</strong>  
    Daily series (Bank Rate, FX, FTSE) are collapsed to the last observation of each
    calendar month. Slower series (GDP growth, crime, wellbeing) report their own
    latest available figure rather than being forced onto the common reference month.</p>

    <p><strong>Volatility.</strong>  
    FTSE 100 and GBP trade-weighted volatility are calculated as the standard
    deviation of daily returns within each calendar month, then accumulated and
    z-scored like any other series.</p>

    <p><strong>Aggregation.</strong>  
    The final UKPI is a weighted average of the oriented z-scores, multiplied by 25
    for presentation only (so ±25 ≈ one standard deviation of the composite).</p>

    <p><strong>Data sources</strong></p>
    <ul>
      <li>ONS – CPI, GDP, public sector net debt, unemployment, vacancies, redundancies, real earnings, crime, wellbeing</li>
      <li>Bank of England – Bank Rate, effective exchange-rate index</li>
      <li>Alpha Vantage – FTSE 100 ETF (ISF.LON) daily prices</li>
      <li>FRED – UK Economic Policy Uncertainty</li>
      <li>GfK / Lloyds Banking Group – Consumer Confidence and Business Barometer (manual)</li>
    </ul>

  </div>

  <footer>
    Last updated {generated_at} &nbsp;·&nbsp;
    <a href="https://github.com/RaphaelMonti/United-Kingdom-Panic-Index">Source on GitHub</a>
  </footer>

</div>
</body>
</html>
"""

if __name__ == "__main__":
    main()
