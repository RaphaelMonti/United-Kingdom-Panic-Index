import requests
import os
import csv
import calendar
import numpy as np
from datetime import datetime

ALPHA_VANTAGE_BASE = "https://www.alphavantage.co/query"
VOLATILITY_HISTORY_PATH = "data/ftse_volatility_history.csv"


def get_ftse_prices() -> list[tuple]:
    """Fetch daily prices for ISF.LON (FTSE 100 ETF proxy) — Alpha Vantage free tier, ~100 days."""
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        raise EnvironmentError("ALPHA_VANTAGE_KEY environment variable not set.")

    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": "ISF.LON",
        "apikey": api_key,
    }
    response = requests.get(ALPHA_VANTAGE_BASE, params=params)
    response.raise_for_status()
    data = response.json()

    if "Error Message" in data:
        raise ValueError(f"Alpha Vantage error: {data['Error Message']}")
    if "Note" in data:
        raise ValueError(f"Alpha Vantage rate limit hit: {data['Note']}")

    series = data.get("Time Series (Daily)")
    if not series:
        raise ValueError(f"Unexpected response format: {list(data.keys())}")

    rows = [
        (datetime.strptime(date_str, "%Y-%m-%d"), float(values["4. close"]))
        for date_str, values in series.items()
    ]
    rows.sort(key=lambda x: x[0])
    return rows


def compute_current_volatility(prices: list[tuple]) -> float:
    """Standard deviation of daily returns over the available price window."""
    values = [v for _, v in prices]
    daily_returns = [(values[i] - values[i - 1]) / values[i - 1] for i in range(1, len(values))]
    return float(np.std(daily_returns))


def load_volatility_history() -> list[tuple]:
    if not os.path.exists(VOLATILITY_HISTORY_PATH):
        return []
    with open(VOLATILITY_HISTORY_PATH, "r") as f:
        reader = csv.DictReader(f)
        rows = [(datetime.strptime(r["date"], "%Y-%m-%d"), float(r["volatility"])) for r in reader]
    rows.sort(key=lambda x: x[0])
    return rows


def append_volatility_reading(date: datetime, volatility: float) -> list[tuple]:
    """Add this month's volatility reading to the growing history, avoiding duplicate months."""
    history = load_volatility_history()

    # Skip if we already have a reading for this month
    if any(d.year == date.year and d.month == date.month for d, _ in history):
        print(f"Volatility reading for {date.strftime('%Y-%m')} already recorded — skipping duplicate.")
        return history

    history.append((date, volatility))
    history.sort(key=lambda x: x[0])

    os.makedirs("data", exist_ok=True)
    with open(VOLATILITY_HISTORY_PATH, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "volatility"])
        for d, v in history:
            writer.writerow([d.strftime("%Y-%m-%d"), v])

    print(f"Added volatility reading for {date.strftime('%Y-%m')}: {volatility:.6f}. Total readings: {len(history)}.")
    return history


def get_ftse_volatility_series() -> list[tuple]:
    """
    Return historical monthly volatility. Append a reading only when the
    fetched daily prices cover a completed calendar month sufficiently.
    """
    prices = sorted(get_ftse_prices(), key=lambda x: x[0])
    today = datetime.now()
    current_month = datetime(today.year, today.month, 1)

    if current_month.month == 1:
        target_year, target_month = current_month.year - 1, 12
    else:
        target_year, target_month = current_month.year, current_month.month - 1

    target_prices = [
        (date, price) for date, price in prices
        if date.year == target_year and date.month == target_month
    ]

    if len(target_prices) < 15:
        print(
            f"Daily prices do not sufficiently cover {target_year}-{target_month:02d}; "
            "historical volatility left unchanged."
        )
        return load_volatility_history()

    if target_prices[0][0].day > 7 or target_prices[-1][0].day < 25:
        print(
            f"Daily prices do not sufficiently cover {target_year}-{target_month:02d}; "
            "historical volatility left unchanged."
        )
        return load_volatility_history()

    prior_prices = [
        (date, price) for date, price in prices
        if (date.year, date.month) < (target_year, target_month)
    ]
    calculation_prices = (
        ([prior_prices[-1]] if prior_prices else []) + target_prices
    )
    volatility = compute_current_volatility(calculation_prices)
    month_end = datetime(
        target_year,
        target_month,
        calendar.monthrange(target_year, target_month)[1],
    )

    append_volatility_reading(month_end, volatility)
    return load_volatility_history()


if __name__ == "__main__":
    history = get_ftse_volatility_series()
    print(f"\nLatest volatility reading: {history[-1]}")
    print(f"Total months of volatility history so far: {len(history)}")