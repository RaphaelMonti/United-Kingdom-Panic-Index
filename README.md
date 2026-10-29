# UK Panic Index (UKPI)

The UK Panic Index is a simple way of answering the question:

> “How stressed does the UK economy look right now compared with its own recent history?”

It takes twelve public indicators covering inflation, growth, debt, interest rates, markets, jobs, confidence and wellbeing, standardises each one against its own past behaviour, and combines them into a single monthly number.

- **Positive reading** → the indicators are, on balance, showing more stress than usual  
- **Negative reading** → the indicators are, on balance, showing less stress than usual  
- **Near zero** → things look roughly normal relative to the last few years  

The index is deliberately relative. It is not a recession probability, a forecast, or a claim that the economy is “good” or “bad” in absolute terms.

Live site: [raphaelmonti.github.io/United-Kingdom-Panic-Index](https://raphaelmonti.github.io/United-Kingdom-Panic-Index/)

---

## How the index is built

### 1. Standardisation

Each indicator is turned into a z-score using a trailing five-year window:

\[
z_t = \frac{x_t - \mu_t}{\sigma_t}
\]

The observation being scored is deliberately left out of its own baseline so it cannot influence the mean and standard deviation it is being compared against. A score of +1 means the latest reading is one historical standard deviation above the recent average; −1 means one standard deviation below.

### 2. Direction adjustment

Not every series moves in the same direction as economic stress. Higher unemployment or higher market volatility usually signals more stress; stronger GDP growth or higher real pay usually signals less. Series of the second type are inverted so that a higher final score always means more stress.

### 3. Composite indicators

Two of the twelve components are themselves blends:

- **Job security** – redundancies + vacancy-to-unemployment ratio  
- **Confidence & uncertainty** – GfK consumer confidence + Lloyds Business Barometer + UK Economic Policy Uncertainty  

This keeps the final aggregation cleaner while still using the information from the underlying series.

### 4. Weighting and aggregation

Each component has a fixed weight. If some series cannot be scored that month (not enough history, missing data, etc.), the remaining weights are simply renormalised. The final index is:

\[
\text{UKPI}_t = 25 \times \frac{\sum_{i \in A_t} w_i z_{i,t}}{\sum_{i \in A_t} w_i}
\]

The ×25 is only for presentation so that ±25 roughly corresponds to one standard deviation of the composite.

---

## Current components

| Component | What it captures |
|-----------|------------------|
| CPI inflation | Price pressures |
| GDP growth | Real economic output |
| Public sector net debt | Fiscal position |
| Bank Rate | Monetary policy stance |
| FTSE volatility | Equity-market stress (via ISF.LON ETF) |
| GBP FX volatility | Sterling volatility |
| Unemployment | Labour-market slack |
| Real pay growth | Purchasing power |
| Job security composite | Redundancies + vacancies |
| Confidence & uncertainty composite | Consumer, business and policy uncertainty |

Exactly which series appear in any given month depends on data availability. The website always shows the components that were actually used for the latest reading.

---

## Data sources

- **ONS** – inflation, GDP, public debt, unemployment, vacancies, redundancies, real earnings, crime, wellbeing  
- **Bank of England** – Bank Rate and effective exchange-rate index  
- **Alpha Vantage** – daily prices for the FTSE 100 ETF proxy  
- **FRED** – UK Economic Policy Uncertainty  
- **GfK / Lloyds Banking Group** – consumer confidence and business barometer (entered manually)

Different series have different publication lags, so some of the inputs will always refer to an earlier period than the reference month of the index.

---

## Repository layout
United-Kingdom-Panic-Index/
├── main.py              # runs the full calculation
├── utils.py             # shared statistical helpers
├── ONS_API.py           # ONS data
├── BOE_API.py           # Bank of England data
├── FTSE_API.py          # FTSE volatility pipeline
├── FRED_API.py          # Economic Policy Uncertainty
├── manual_data.py       # GfK & Lloyds series
├── generate_site.py     # turns the output into index.html
├── data/                # historical CSVs and model output
└── index.html           # the live website

---

## Running it yourself

git clone https://github.com/RaphaelMonti/United-Kingdom-Panic-Index.git
cd United-Kingdom-Panic-Index

python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

python main.py                     # calculates the index → data/ukpi_output.json
python generate_site.py            # regenerates index.html

---

## Limitations (please read)

This is an experimental research project, not an official statistic.

- Everything is relative to each series’ own recent history, not to any absolute “healthy” level.
- Changing the weights changes the number.
- Missing data changes the effective weights from month to month.
- Some series are published with long lags or are later revised.
- The FTSE component uses an ETF proxy, not the official FTSE 100 index.
- Several components overlap conceptually.
- Direction rules, window length and composite construction are modelling choices.

Always look at the individual component scores as well as the headline number.

---

## Disclaimer

The UK Panic Index is an independent research project. It is not an official statistic, investment advice, economic forecast, or substitute for professional analysis. Results depend on the quality of the source data and on the assumptions built into the model.

---

**Author:** Raphael Monti  
**Repository:** [github.com/RaphaelMonti/United-Kingdom-Panic-Index](https://github.com/RaphaelMonti/United-Kingdom-Panic-Index)
