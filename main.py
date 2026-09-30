import numpy as np
from datetime import datetime
from collections import defaultdict

from ONS_API import (
    get_cpi, get_gdp_growth, get_public_debt_pct_gdp,
    get_unemployment_rate, get_job_security_inputs, get_real_purchasing_power
)
from BOE_API import get_bank_rate, get_gbp_exchange_rate
from FRED_API import get_epu
from FTSE_API import get_ftse_volatility_series
from manual_data import get_gfk_cci, get_lloyds_business_barometer, get_crime_rate, get_wellbeing
from utils import trailing_zscore, find_reference_month, value_as_of, history_as_of


# Derived series (built before gathering, since they
# need raw daily data transformed into monthly readings first)

def build_gbp_fx_volatility_series(fx_series: list[tuple]) -> list[tuple]:
    """Build a monthly volatility series from full daily FX history."""
    by_month = defaultdict(list)
    for date, price in fx_series:
        by_month[(date.year, date.month)].append(price)

    monthly_volatility = []
    for (year, month), prices in sorted(by_month.items()):
        if len(prices) < 5:  # skip incomplete months
            continue
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        monthly_volatility.append((datetime(year, month, 1), float(np.std(returns))))

    return monthly_volatility


# Pull raw data for every indicator (dated tuples)

def gather_raw_data() -> dict:
    js = get_job_security_inputs()
    return {
        "cpi": get_cpi(),
        "gdp_growth": get_gdp_growth(),                                        # Group B
        "public_debt": get_public_debt_pct_gdp(),
        "bank_rate": get_bank_rate(),
        "gbp_fx_volatility": build_gbp_fx_volatility_series(get_gbp_exchange_rate()),
        "unemployment": get_unemployment_rate(),
        "redundancy": js["redundancy"],
        "vacancy_ratio": js["vacancy_ratio"],
        "purchasing_power": get_real_purchasing_power(),
        "epu": get_epu(),
        "ftse_volatility": get_ftse_volatility_series(),                       # already monthly
        "cci": get_gfk_cci(),
        "business_barometer": get_lloyds_business_barometer(),
        "crime_rate": get_crime_rate(),                                        # Group B
        "wellbeing": get_wellbeing(),                                          # Group B
    }


# Group A / Group B split + reference month alignment

GROUP_B_KEYS = {"gdp_growth", "crime_rate", "wellbeing"}

def align_group_a(raw: dict) -> tuple[dict, datetime]:
    """Align all Group A series to the oldest available 'latest date' among them."""
    group_a = {k: v for k, v in raw.items() if k not in GROUP_B_KEYS and k not in ("redundancy", "vacancy_ratio")}
    reference_month = find_reference_month(group_a)

    aligned = {}
    for key, series in group_a.items():
        aligned[key] = value_as_of(series, reference_month)
    return aligned, reference_month


# Direction fixing + z-scoring
# "direct" = higher raw value is worse (bad = high)
# "invert" = higher raw value is better (bad = low)

INDICATOR_DIRECTIONS = {
    "cpi": "direct",
    "gdp_growth": "invert",
    "public_debt": "direct",
    "bank_rate": "direct",
    "gbp_fx_volatility": "direct",
    "unemployment": "direct",
    "redundancy": "direct",
    "vacancy_ratio": "invert",
    "purchasing_power": "invert",
    "epu": "direct",
    "ftse_volatility": "direct",
    "cci": "invert",
    "business_barometer": "invert",
    "crime_rate": "direct",
    "wellbeing": "direct",
}


def zscore_and_orient(key: str, values: list[float]) -> float:
    """Z-score a series and flip sign so higher = more panic, consistently."""
    z = trailing_zscore(values)
    if INDICATOR_DIRECTIONS[key] == "invert":
        z = -z
    return z


# Job Security Proxy (recombines redundancy + vacancy_ratio)

def compute_job_security(raw: dict, reference_month: datetime) -> float:
    """Combine redundancy + vacancy_ratio into one Job Security Proxy score."""
    redundancy_history = history_as_of(raw["redundancy"], reference_month)
    vacancy_history = history_as_of(raw["vacancy_ratio"], reference_month)

    z_redundancy = zscore_and_orient("redundancy", redundancy_history)
    z_vacancy = zscore_and_orient("vacancy_ratio", vacancy_history)

    return (z_redundancy + z_vacancy) / 2

# Composite Sentiment (blends CCI + Business Barometer + EPU)

def compute_composite_sentiment(raw: dict, reference_month: datetime) -> float:
    cci_history = history_as_of(raw["cci"], reference_month)
    barometer_history = history_as_of(raw["business_barometer"], reference_month)
    epu_history = history_as_of(raw["epu"], reference_month)

    z_cci = zscore_and_orient("cci", cci_history)
    z_barometer = zscore_and_orient("business_barometer", barometer_history)
    z_epu = zscore_and_orient("epu", epu_history)

    return (z_cci + z_barometer + z_epu) / 3


# Pillar weights and final aggregation

PILLAR_WEIGHTS = {
    "cpi": 20/3, "gdp_growth": 20/3, "public_debt": 20/3,                          # Pillar 1: 20%
    "bank_rate": 20/3, "ftse_volatility": 20/3, "gbp_fx_volatility": 20/3,          # Pillar 2: 20%
    "unemployment": 7.5, "job_security": 7.5,                                       # Pillar 3: 15%
    "composite_sentiment": 25,                                                      # Pillar 4: 25%
    "crime_rate": 20/3, "purchasing_power": 20/3, "wellbeing": 20/3,               # Pillar 5: 20%
}


def compute_ukpi(raw: dict) -> dict:
    aligned, reference_month = align_group_a(raw)

    # Group A indicators (excluding job security's raw components, sentiment's raw components)
    simple_keys = ["cpi", "public_debt", "bank_rate", "ftse_volatility",
                   "gbp_fx_volatility", "unemployment", "purchasing_power"]

    scores = {}
    for key in simple_keys:
        history = history_as_of(raw[key], reference_month)
        scores[key] = zscore_and_orient(key, history)

    # Job Security (combined)
    scores["job_security"] = compute_job_security(raw, reference_month)

    # Composite Sentiment (combined)
    scores["composite_sentiment"] = compute_composite_sentiment(raw, reference_month)

    # Group B indicators — own latest value, own history, NOT aligned to reference_month
    for key in ["gdp_growth", "crime_rate", "wellbeing"]:
        full_history = [v for _, v in raw[key]]
        scores[key] = zscore_and_orient(key, full_history)

    # Weighted sum
    weighted_sum = sum(scores[k] * (PILLAR_WEIGHTS[k] / 100) for k in scores)

    # Rescale: 0 = long-run average, positive = more panic, negative = calmer than normal
    UKPI_SCALE = 25  # each 1 std of weighted z-score = 25 points, for visible sensitivity
    ukpi_value = weighted_sum * UKPI_SCALE

    return {
        "ukpi": ukpi_value,
        "reference_month": reference_month,
        "component_scores": scores,
    }


if __name__ == "__main__":
    raw = gather_raw_data()
    result = compute_ukpi(raw)

    print(f"\n{'='*50}")
    print(f"UK PANIC INDEX (UKPI): {result['ukpi']:+.2f}")
    print(f"Reference month (Group A): {result['reference_month'].strftime('%Y-%m')}")
    print(f"{'='*50}\n")
    print("Component z-scores (higher = more panic):")
    for key, score in result["component_scores"].items():
        print(f"  {key}: {score:+.3f}")
