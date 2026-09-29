import csv
import os
from datetime import datetime

DATA_DIR = "data"


def load_manual_series(filename: str, max_age_days: int = 120, label: str = "") -> list[tuple]:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"{filepath} not found. Create it with columns 'date,value' "
            f"and add each release's published figure by hand."
        )

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader if row.get("value")]

    if not rows:
        raise ValueError(f"{filepath} has no data rows yet.")

    dated_rows = [(datetime.strptime(r["date"], "%Y-%m-%d"), float(r["value"])) for r in rows]
    dated_rows.sort(key=lambda x: x[0])

    age_days = (datetime.now() - dated_rows[-1][0]).days
    if age_days > max_age_days:
        print(f"⚠️  WARNING: {label or filename} is stale — last manual entry is {dated_rows[-1][0].date()} ({age_days} days old)")

    return dated_rows


def get_gfk_cci() -> list[tuple]:
    return load_manual_series("gfk_cci.csv", max_age_days=60, label="GfK CCI")

def get_lloyds_business_barometer() -> list[tuple]:
    return load_manual_series("lloyds_business_barometer.csv", max_age_days=60, label="Lloyds Business Barometer")

def get_crime_rate() -> list[tuple]:
    return load_manual_series("crime_rate.csv", max_age_days=120, label="Crime Rate")

def get_wellbeing() -> list[tuple]:
    return load_manual_series("wellbeing.csv", max_age_days=120, label="Wellbeing (ONS4)")