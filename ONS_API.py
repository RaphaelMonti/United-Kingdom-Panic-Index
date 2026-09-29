import requests
from utils import check_freshness, parse_ons_date

ONS_BASE = "https://api.beta.ons.gov.uk/v1/data"


def get_series(uri: str) -> list[dict]:
    response = requests.get(ONS_BASE, params={"uri": uri})
    response.raise_for_status()
    data = response.json()
    if data.get("months"):
        return data["months"]
    elif data.get("quarters"):
        return data["quarters"]
    elif data.get("years"):
        return data["years"]
    else:
        raise ValueError(f"No observations found for {uri}")


def _dated_values(uri: str, max_age_days: int = 90, label: str = "") -> list[tuple]:
    raw = get_series(uri)
    clean = [m for m in raw if m.get("value") not in ("", None)]
    if not clean:
        raise ValueError(f"No usable data returned for {uri}")
    check_freshness(clean[-1]["date"], max_age_days=max_age_days, label=label or uri)
    return [(parse_ons_date(m["date"]), float(m["value"])) for m in clean]


def get_cpi() -> list[tuple]:
    return _dated_values("/economy/inflationandpriceindices/timeseries/d7g7/mm23", max_age_days=85, label="CPI")


def get_gdp_growth() -> list[tuple]:
    return _dated_values("/economy/grossdomesticproductgdp/timeseries/ihyq/pn2", max_age_days=270, label="GDP Growth")


def get_public_debt_pct_gdp() -> list[tuple]:
    return _dated_values("/economy/governmentpublicsectorandtaxes/publicsectorfinance/timeseries/hf6x/pusf", max_age_days=85, label="Public Debt % GDP")


def get_unemployment_rate() -> list[tuple]:
    return _dated_values("/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/mgsx/lms", max_age_days=150, label="Unemployment Rate")


def get_job_security_inputs() -> dict:
    redundancy = _dated_values("/employmentandlabourmarket/peoplenotinwork/redundancies/timeseries/beir/lms", max_age_days=150, label="Redundancy Rate")
    vacancies = _dated_values("/employmentandlabourmarket/peopleinwork/employmentandemployeetypes/timeseries/ap2y/lms", max_age_days=110, label="Vacancies")
    unemployment = _dated_values("/employmentandlabourmarket/peoplenotinwork/unemployment/timeseries/mgsc/lms", max_age_days=150, label="Unemployment Level")

    # Align vacancies/unemployment by matching dates, then build the ratio
    unemployment_dict = dict(unemployment)
    vacancy_ratio = [
        (date, val / unemployment_dict[date])
        for date, val in vacancies
        if date in unemployment_dict
    ]

    return {"redundancy": redundancy, "vacancy_ratio": vacancy_ratio}


def get_real_purchasing_power() -> list[tuple]:
    return _dated_values("/employmentandlabourmarket/peopleinwork/earningsandworkinghours/timeseries/a3wx/emp", max_age_days=150, label="Real Purchasing Power")


if __name__ == "__main__":
    print("CPI:", get_cpi()[-1])
    print("GDP Growth:", get_gdp_growth()[-1])
    print("Public Debt:", get_public_debt_pct_gdp()[-1])
    print("Unemployment:", get_unemployment_rate()[-1])
    js = get_job_security_inputs()
    print("Redundancy:", js["redundancy"][-1])
    print("Vacancy Ratio:", js["vacancy_ratio"][-1])
    print("Purchasing Power:", get_real_purchasing_power()[-1])