import requests
import csv
from io import StringIO
from datetime import datetime

FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def check_freshness_fred(date_str: str, max_age_days: int = 90, label: str = "") -> int:
    latest = datetime.strptime(date_str, "%Y-%m-%d")
    age_days = (datetime.now() - latest).days
    if age_days > max_age_days:
        print(f"⚠️  WARNING: {label} data is stale — latest observation is '{date_str}' ({age_days} days old)")
    return age_days


def get_epu() -> list[tuple]:
    response = requests.get(FRED_BASE, params={"id": "UKEPUINDXM"})
    response.raise_for_status()
    reader = csv.DictReader(StringIO(response.text))
    rows = []
    for row in reader:
        value = row.get("UKEPUINDXM")
        if value and value != ".":
            rows.append((datetime.strptime(row["observation_date"], "%Y-%m-%d"), float(value)))
    if not rows:
        raise ValueError("No EPU data returned from FRED")
    check_freshness_fred(rows[-1][0].strftime("%Y-%m-%d"), max_age_days=90, label="UK EPU")
    return rows


if __name__ == "__main__":
    print("EPU:", get_epu()[-1])