from datetime import datetime
import numpy as np

def trailing_zscore(values: list[float], window_years: int = 10, periods_per_year: int = 12) -> float:
    window = window_years * periods_per_year
    recent = values[-window:] if len(values) >= window else values
    mean = np.mean(recent)
    std = np.std(recent)
    latest = values[-1]
    return (latest - mean) / std if std != 0 else 0.0


MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def parse_ons_date(date_str: str) -> datetime:
    date_str = date_str.strip().upper()
    parts = date_str.split()
    if len(parts) == 2 and parts[1] in MONTH_MAP:
        return datetime(int(parts[0]), MONTH_MAP[parts[1]], 1)
    elif len(parts) == 2 and parts[1].startswith("Q"):
        quarter = int(parts[1][1])
        month = (quarter - 1) * 3 + 1
        return datetime(int(parts[0]), month, 1)
    elif len(parts) == 1:
        return datetime(int(parts[0]), 1, 1)
    else:
        raise ValueError(f"Unrecognized date format: {date_str}")


def parse_boe_date(date_str: str) -> datetime:
    date_str = date_str.strip().upper()
    day, month_str, year = date_str.split()
    return datetime(int(year), MONTH_MAP[month_str], int(day))


def check_freshness(date_str: str, max_age_days: int = 90, label: str = "") -> int:
    latest = parse_ons_date(date_str)
    age_days = (datetime.now() - latest).days
    if age_days > max_age_days:
        print(f"⚠️  WARNING: {label} data is stale — latest observation is '{date_str}' ({age_days} days old)")
    return age_days


def check_freshness_boe(date_str: str, max_age_days: int = 90, label: str = "") -> int:
    latest = parse_boe_date(date_str)
    age_days = (datetime.now() - latest).days
    if age_days > max_age_days:
        print(f"⚠️  WARNING: {label} data is stale — latest observation is '{date_str}' ({age_days} days old)")
    return age_days


# --- NEW: month-alignment logic ---

def find_reference_month(all_series: dict[str, list[tuple[datetime, float]]]) -> datetime:
    """Find the oldest 'latest available' date across all indicators — this becomes the common reference point."""
    latest_dates = [series[-1][0] for series in all_series.values() if series]
    if not latest_dates:
        raise ValueError("No series provided")
    return min(latest_dates)


def value_as_of(series: list[tuple[datetime, float]], reference_date: datetime) -> float:
    """Most recent value at or before reference_date (hold-flat for slower-updating series)."""
    eligible = [v for d, v in series if d <= reference_date]
    if not eligible:
        raise ValueError(f"No data available as of {reference_date}")
    return eligible[-1]
def value_as_of(series: list[tuple[datetime, float]], reference_date: datetime) -> float:
    """Most recent value at or before reference_date. Falls back to the earliest
    available value (with a warning) if the series starts later than reference_date —
    this happens for brand-new series still accumulating history."""
    eligible = [v for d, v in series if d <= reference_date]
    if eligible:
        return eligible[-1]
def history_as_of(series: list[tuple[datetime, float]], reference_date: datetime) -> list[float]:
    """Full value history up to reference_date. Falls back to the full series
    if nothing qualifies (brand-new series that starts after reference_date)."""
    eligible = [v for d, v in series if d <= reference_date]
    if eligible:
        return eligible
    if series:
        print(f"WARNING: no history at or before {reference_date.date()} — using full available series instead.")
        return [v for _, v in series]
    raise ValueError("No data available at all for this series")

    if series:
        earliest_date, earliest_value = series[0]
        print(f"⚠️  WARNING: no data at or before {reference_date.date()} — "
              f"using earliest available value from {earliest_date.date()} instead.")
        return earliest_value

    raise ValueError("No data available at all for this series")
