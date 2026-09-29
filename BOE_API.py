import requests
import csv
from io import StringIO
from utils import trailing_zscore, check_freshness_boe, parse_boe_date

BOE_BASE = "https://www.bankofengland.co.uk/boeapps/database/_iadb-fromshowcolumns.asp"


def get_boe_series(series_code: str, date_from: str = "01/Jan/2015", date_to: str = "01/Jan/2030") -> list[tuple]:
    params = {
        "csv.x": "yes", "Datefrom": date_from, "Dateto": date_to,
        "SeriesCodes": series_code, "CSVF": "TN",
        "UsingCodes": "Y", "VPD": "Y", "VFD": "N",
    }
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(BOE_BASE, params=params, headers=headers)
    response.raise_for_status()

    reader = csv.reader(StringIO(response.text))
    rows = []
    for row in reader:
        if len(row) >= 2:
            try:
                rows.append((row[0], float(row[1])))
            except ValueError:
                continue
    return rows


def get_bank_rate() -> list[tuple]:
    rows = get_boe_series("IUDBEDR")
    check_freshness_boe(rows[-1][0], max_age_days=90, label="Bank Rate")
    return [(parse_boe_date(d), v) for d, v in rows]


def get_gbp_exchange_rate() -> list[tuple]:
    rows = get_boe_series("XUDLBK67")
    check_freshness_boe(rows[-1][0], max_age_days=10, label="GBP Exchange Rate")
    return [(parse_boe_date(d), v) for d, v in rows]


if __name__ == "__main__":
    print("Bank Rate:", get_bank_rate()[-1])
    print("GBP FX:", get_gbp_exchange_rate()[-1])