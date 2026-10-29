
import json
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "ukpi_output.json"
OUTPUT_FILE = ROOT / "index.html"

LABELS = {
    "cpi": "CPI inflation",
    "gdp_growth": "GDP growth",
    "public_debt": "Public sector net debt",
    "bank_rate": "Bank Rate",
    "ftse_volatility": "FTSE volatility (ETF proxy)",
    "gbp_fx_volatility": "GBP exchange-rate volatility",
    "unemployment": "Unemployment rate",
    "purchasing_power": "Real pay growth",
    "job_security": "Job security composite",
    "composite_sentiment": "Confidence and uncertainty",
}


def fmt(value, digits=3):
    value = float(value)
    return ("+" if value >= 0 else "−") + f"{abs(value):.{digits}f}"


def score_class(value):
    if value > 0.05:
        return "stress"
    if value < -0.05:
        return "calm"
    return "neutral"


def build_rows(scores, weights):
    rows = []
    for key, value in sorted(
        scores.items(), key=lambda item: float(item[1]), reverse=True
    ):
        value = float(value)
        label = LABELS.get(key, key.replace("_", " ").title())
        weight = float(weights.get(key, 0))
        width = min(abs(value) / 2 * 50, 50)
        bar_class = "positive" if value >= 0 else "negative"
        bar_style = (
            f"left:50%;width:{width:.2f}%"
            if value >= 0
            else f"right:50%;width:{width:.2f}%"
        )

        rows.append(
            f"<tr>"
            f"<td>{escape(label)}</td>"
            f'<td><div class="track"><span class="bar {bar_class}" '
            f'style="{bar_style}"></span></div></td>'
            f'<td class="num {score_class(value)}">{fmt(value)}</td>'
            f'<td class="num">{weight * 100:.2f}%</td>'
            f"</tr>"
        )
    return "\n".join(rows)


def main():
    if not DATA_FILE.exists():
        raise FileNotFoundError(
            "data/ukpi_output.json is missing. Run the UKPI model first."
        )

    with DATA_FILE.open(encoding="utf-8") as file:
        data = json.load(file)

    scores = data.get("component_scores", {})
    weights = data.get("weights_used", {})
    if not scores:
        raise ValueError("No component scores found in ukpi_output.json.")

    score = float(data["ukpi"])
    ref_month = escape(str(data.get("reference_month", "Unknown")))
    generated = escape(str(data.get("generated_at", "Unknown")))
    count = len(scores)

    if weights:
        total = sum(float(weights.get(key, 0)) for key in scores)
        if abs(total - 1) > 0.02:
            print(f"Warning: displayed weights sum to {total:.3f}, not 1.000.")

    template = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>UK Panic Index</title>
<style>
*{box-sizing:border-box}
body{margin:0;font:14px/1.55 Arial,Helvetica,sans-serif;color:#292e33;background:#fff}
header{background:#303438;color:white}
.top{max-width:1120px;margin:auto;padding:13px 22px;display:flex;justify-content:space-between;gap:20px}
.brand{font-weight:bold;letter-spacing:.3px}
nav{display:flex;gap:20px}
a{color:inherit;text-decoration:none}
a:hover{text-decoration:underline}
nav a{color:#ddd}
.title{background:#477db8;color:white;padding:12px 22px;font-size:20px;font-weight:bold}
.title div{max-width:1120px;margin:auto}
main{max-width:1120px;margin:auto;padding:25px 22px 42px}
h1{font-size:25px;margin:0 0 5px}
h2{font-size:17px;margin:28px 0 12px;padding-bottom:7px;border-bottom:1px solid #dce1e5}
h3{font-size:14px;margin:18px 0 5px}
p{margin:6px 0 12px}
.subtitle,.muted{color:#68727d}
.subtitle{margin-bottom:22px}
.muted{font-size:12px}
.summary{display:grid;grid-template-columns:250px 1fr;border:1px solid #dce1e5;margin-bottom:25px}
.summary>div{padding:18px 20px}
.summary>div+div{border-left:1px solid #dce1e5}
.label{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:#68727d;font-weight:bold}
.score{font-size:39px;font-weight:bold;line-height:1.2;margin:5px 0}
.stress{color:#bd4a45}.calm{color:#27816b}.neutral{color:#292e33}
.grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(280px,1fr);gap:28px;align-items:start}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f5f6f7;color:#5d6670;font-size:12px;font-weight:normal;text-align:left}
th,td{padding:9px 8px;border-bottom:1px solid #e8ebee}
tr:hover td{background:#fafbfc}
.num{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}
.track{height:10px;background:#f0f2f4;position:relative;min-width:65px}
.track:after{content:"";position:absolute;left:50%;top:-3px;height:16px;border-left:1px solid #8d969f}
.bar{position:absolute;top:0;height:10px}
.positive{background:#bd4a45}.negative{background:#27816b}
.formula{background:#f5f6f7;padding:10px 12px;margin:8px 0 12px;overflow-wrap:anywhere}
ul{padding-left:20px;color:#414951}
li{margin:4px 0}
.note{margin-top:22px;padding-top:13px;border-top:1px solid #dce1e5;color:#68727d;font-size:12px}
footer{border-top:1px solid #dce1e5;padding:16px 22px;color:#68727d;font-size:12px}
.footer-inner{max-width:1120px;margin:auto;display:flex;justify-content:space-between;gap:15px}
footer a{color:#477db8}
@media(max-width:760px){
.top{flex-direction:column}
nav{flex-wrap:wrap}
main{padding:22px 13px 35px}
.summary,.grid{grid-template-columns:1fr}
.summary>div+div{border-left:0;border-top:1px solid #dce1e5}
.grid{gap:5px}
th,td{padding:8px 5px}
.track{min-width:40px}
.footer-inner{flex-direction:column}
}
</style>
</head>
<body>
<header><div class="top">
<a class="brand" href="#">UK PANIC INDEX</a>
<nav><a href="#readings">Readings</a><a href="#methodology">Methodology</a>
<a href="https://github.com/RaphaelMonti/United-Kingdom-Panic-Index">Source code ↗</a></nav>
</div></header>
<div class="title"><div>United Kingdom — Economic stress indicator</div></div>
<main>
<h1>Economic stress and uncertainty</h1>
<p class="subtitle">A composite indicator built from public economic and financial data.</p>
<div class="summary">
<div>
<div class="label">Latest index reading</div>
<div class="score __CLASS__">__SCORE__</div>
<div class="muted">Reference month: __MONTH__</div>
<div class="muted">__COUNT__ components scored</div>
</div>
<div>
<div class="label">Interpretation</div>
<p>Positive readings indicate that the weighted indicators, after direction adjustment, are above their historical baselines on balance.</p>
<p class="muted">The UKPI is a research indicator, not a probability, percentage, official statistic or forecast.</p>
</div>
</div>

<div class="grid">
<section id="readings">
<h2>Component readings</h2>
<p class="muted">Zero is the baseline. Bars are visually capped at ±2 standardised units.</p>
<table><thead><tr><th>Indicator</th><th>Score</th><th class="num">Value</th><th class="num">Weight</th></tr></thead>
<tbody>__ROWS__</tbody></table>
</section>

<section id="methodology">
<h2>Methodology</h2>
<h3>1. Indicators</h3>
<p>The model currently scores __COUNT__ components covering prices, output, public debt, monetary conditions, financial volatility, employment, real pay, job security, and confidence or policy uncertainty. Job security and confidence are composites built from multiple source series.</p>

<h3>2. Standardisation</h3>
<p>Each series is compared with its preceding five-year history. The observation being scored is excluded from the baseline. The model uses a z-score:</p>
<div class="formula">z = (observation − baseline mean) ÷ baseline standard deviation</div>
<p>A score of +1 means one baseline standard deviation above its historical mean; −1 means one below. A series cannot be scored when its baseline is insufficient or has no variation.</p>

<h3>3. Direction adjustment</h3>
<p>Signs are adjusted so higher component scores are intended to represent greater stress. Higher unemployment and volatility increase stress, while stronger GDP growth and real pay growth are inverted. These are modelling assumptions; relationships are not always one-directional.</p>

<h3>4. Composite components</h3>
<p><strong>Job security</strong> combines redundancies and the vacancy-to-unemployment ratio, with the latter direction-adjusted. <strong>Confidence and uncertainty</strong> combines consumer confidence, the business barometer and economic policy uncertainty. It can be scored when at least two of its three inputs are available.</p>

<h3>5. Weights and aggregation</h3>
<p>Each available component is multiplied by its configured weight. Weights are renormalised across components that can be scored, so effective weights sum to 100%. Missing indicators are not treated as zero, but the mix of the index may change between months.</p>
<div class="formula">Displayed UKPI = weighted average of component z-scores × 25</div>
<p>The factor of 25 is a presentation scale, not a percentage or probability. It does not correspond to a specific real-world outcome.</p>

<h3>6. Reporting period and data lags</h3>
<p>The intended live reference month is the last completed calendar month. Some series are published less frequently than monthly or arrive with delays. Their latest available observation may therefore describe an earlier period. The period an observation describes is not necessarily its publication date.</p>

<h3>7. Interpretation and limitations</h3>
<p>The score measures conditions relative to each indicator's own recent history. It does not directly measure household hardship, financial losses, recession probability or absolute economic health. Indicator overlap, source revisions, missing data, proxy choices and weights can affect results. Historical comparisons and alternative weighting schemes should be tested before drawing strong conclusions.</p>

<h3>Data sources</h3>
<ul>
<li>ONS: inflation, GDP, public debt, labour-market data and earnings.</li>
<li>Bank of England: Bank Rate and exchange-rate data.</li>
<li>FTSE volatility input: ISF.LON ETF price proxy, not a direct FTSE 100 index series.</li>
<li>FRED: UK Economic Policy Uncertainty.</li>
<li>GfK and Lloyds Banking Group: consumer confidence and business barometer data.</li>
</ul>
</section>
</div>
<p class="note">Generated from model output at __GENERATED__. Data may be revised. This page updates when the model output is regenerated and the site is republished.</p>
</main>
<footer><div class="footer-inner"><span>UK Panic Index · Independent research project</span>
<a href="https://github.com/RaphaelMonti/United-Kingdom-Panic-Index">Code and data on GitHub ↗</a></div></footer>
</body></html>
"""

    replacements = {
        "__CLASS__": score_class(score),
        "__SCORE__": escape(fmt(score, 2)),
        "__MONTH__": ref_month,
        "__COUNT__": str(count),
        "__ROWS__": build_rows(scores, weights),
        "__GENERATED__": generated,
    }

    for token, value in replacements.items():
        template = template.replace(token, value)

    OUTPUT_FILE.write_text(template, encoding="utf-8")
    print(
        f"Generated index.html — UKPI {fmt(score, 2)}, "
        f"reference {ref_month}, {count} components"
    )


if __name__ == "__main__":
    main()
