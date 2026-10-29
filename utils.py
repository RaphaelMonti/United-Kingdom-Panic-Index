
from datetime import datetime
import numpy as np


def trailing_zscore(
    series: list[tuple[datetime, float]],
    reference_date: datetime,
    window_years: int = 5,
    min_observations: int = 24,
) -> float:
    """
    Score the latest observation against earlier observations in the
    preceding calendar window. The scored observation is excluded
    from its own baseline.
    """
    if window_years <= 0:
        raise ValueError("window_years must be positive")

    eligible = sorted(
        [(date, float(value)) for date, value in series
         if date <= reference_date],
        key=lambda item: item[0],
    )

    if len(eligible) < 2:
        raise ValueError("At least two dated observations are required")

    latest_date, latest_value = eligible[-1]

    try:
        window_start = latest_date.replace(
            year=latest_date.year - window_years
        )
    except ValueError:
        window_start = latest_date.replace(
            year=latest_date.year - window_years,
            day=28,
        )

    baseline = [
        value for date, value in eligible
        if window_start <= date < latest_date
    ]

    if len(baseline) < min_observations:
        raise ValueError(
            f"Insufficient baseline observations: {len(baseline)} "
            f"found, {min_observations} required"
        )

    mean = float(np.mean(baseline))
    std = float(np.std(baseline, ddof=0))

    if std == 0:
        raise ValueError("Baseline has zero variance")

    return (latest_value - mean) / std


MONTH_MAP = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
}


def parse_ons_date(date_str: str) -> datetime:
    date_str = date_str.strip().upper()
    parts = date_str.split()

    if len(parts) == 2 and parts[1] in MONTH_MAP:
        return datetime(int(parts[0]), MONTH_MAP[parts[1]], 1)

    if len(parts) == 2 and parts[1].startswith("Q"):
        quarter = int(parts[1][1])
        if quarter not in (1, 2, 3, 4):
            raise ValueError(f"Invalid quarter: {date_str}")
        month = (quarter - 1) * 3 + 1
        return datetime(int(parts[0]), month, 1)

    if len(parts) == 1:
        return datetime(int(parts[0]), 1, 1)

    raise ValueError(f"Unrecognized date format: {date_str}")


def parse_boe_date(date_str: str) -> datetime:
    date_str = date_str.strip().upper()
    day, month_str, year = date_str.split()
    return datetime(int(year), MONTH_MAP[month_str], int(day))


def check_freshness(
    date_str: str,
    max_age_days: int = 90,
    label: str = "",
) -> int:
    latest = parse_ons_date(date_str)
    age_days = (datetime.now() - latest).days

    if age_days > max_age_days:
        print(
            f"WARNING: {label} data is stale — "
            f"latest observation is '{date_str}' ({age_days} days old)"
        )

    return age_days


def check_freshness_boe(
    date_str: str,
    max_age_days: int = 90,
    label: str = "",
) -> int:
    latest = parse_boe_date(date_str)
    age_days = (datetime.now() - latest).days

    if age_days > max_age_days:
        print(
            f"WARNING: {label} data is stale — "
            f"latest observation is '{date_str}' ({age_days} days old)"
        )

    return age_days


def find_reference_month(
    all_series: dict[str, list[tuple[datetime, float]]],
) -> datetime:
    """Return the end of the last completed calendar month."""
    from calendar import monthrange

    if not any(all_series.values()):
        raise ValueError("No series provided")

    today = datetime.now()
    if today.month == 1:
        year, month = today.year - 1, 12
    else:
        year, month = today.year, today.month - 1

    last_day = monthrange(year, month)[1]
    return datetime(year, month, last_day)


def value_as_of(
    series: list[tuple[datetime, float]],
    reference_date: datetime,
) -> float:
    """Return the most recent value at or before the reference date."""
    eligible = sorted(
        [(date, value) for date, value in series if date <= reference_date],
        key=lambda item: item[0],
    )

    if eligible:
        return eligible[-1][1]

    raise ValueError(
        f"No observations available on or before {reference_date.date()}"
    )


def history_as_of(
    series: list[tuple[datetime, float]],
    reference_date: datetime,
) -> list[float]:
    """Return values observed on or before the reference date."""
    return [
        value for date, value in sorted(series, key=lambda item: item[0])
        if date <= reference_date
    ]


def dated_history_as_of(
    series: list[tuple[datetime, float]],
    reference_date: datetime,
) -> list[tuple[datetime, float]]:
    """Return dated observations on or before the reference date."""
    return sorted(
        [(date, value) for date, value in series if date <= reference_date],
        key=lambda item: item[0],
    )
