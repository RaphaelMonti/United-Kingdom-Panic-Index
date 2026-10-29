import json
from collections import defaultdict
from datetime import datetime

import numpy as np

from ONS_API import (
    get_cpi, get_gdp_growth, get_public_debt_pct_gdp,
    get_unemployment_rate, get_job_security_inputs, get_real_purchasing_power,
)
from BOE_API import get_bank_rate, get_gbp_exchange_rate
from FRED_API import get_epu
from FTSE_API import get_ftse_volatility_series
from manual_data import (
    get_gfk_cci, get_lloyds_business_barometer, )
from utils import trailing_zscore, find_reference_month

Series = list[tuple[datetime, float]]

UKPI_SCALE = 25  # presentation multiplier only, not a statistical claim


# ------------------------------------------------------------
# Frequency handling: every series is monthly or slower before scoring
# ------------------------------------------------------------

def monthly_last(series: Series) -> Series:
    """Collapse a daily series to its last observation in each calendar month."""
    by_month = {}
    for date, value in sorted(series, key=lambda x: x[0]):
        by_month[(date.year, date.month)] = (date, value)
    return [by_month[k] for k in sorted(by_month)]


def build_gbp_fx_volatility_series(fx_series: Series) -> Series:
    """Monthly volatility = std dev of daily returns within each calendar month."""
    by_month = defaultdict(list)
    for date, price in sorted(fx_series, key=lambda x: x[0]):
        by_month[(date.year, date.month)].append(price)

    out = []
    for (year, month), prices in sorted(by_month.items()):
        if len(prices) < 5:
            continue
        returns = [(prices[i] - prices[i - 1]) / prices[i - 1] for i in range(1, len(prices))]
        out.append((datetime(year, month, 1), float(np.std(returns))))
    return out


def yoy_growth(series: Series) -> Series:
    """Year-on-year % change from a monthly level series."""
    by_date = dict(series)
    out = []
    for date, value in sorted(series, key=lambda x: x[0]):
        prior = by_date.get(date.replace(year=date.year - 1))
        if prior:
            out.append((date, (value / prior - 1) * 100))
    return out


def gather_raw_data() -> dict:
    js = get_job_security_inputs()
    return {
        "cpi": get_cpi(),
        "gdp_growth": get_gdp_growth(),
        "public_debt": get_public_debt_pct_gdp(),
        "bank_rate": monthly_last(get_bank_rate()),
        "gbp_fx_volatility": build_gbp_fx_volatility_series(get_gbp_exchange_rate()),
        "unemployment": get_unemployment_rate(),
        "redundancy": js["redundancy"],
        "vacancy_ratio": js["vacancy_ratio"],
        "purchasing_power": get_real_purchasing_power(),
        "epu": get_epu(),
        "ftse_volatility": get_ftse_volatility_series(),
        "cci": get_gfk_cci(),
        "business_barometer": get_lloyds_business_barometer(),
    }


# ------------------------------------------------------------
# Direction, grouping, weights
# ------------------------------------------------------------

# "direct" = higher raw value is worse; "invert" = higher raw value is better
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
}

GROUP_B = {"gdp_growth"}  # slow series, scored at their own latest date

SIMPLE_GROUP_A = [
    "cpi", "public_debt", "bank_rate", "ftse_volatility",
    "gbp_fx_volatility", "unemployment", "purchasing_power",
]

# (name, component series, minimum components that must be scorable)
COMPOSITES = [
    ("job_security", ["redundancy", "vacancy_ratio"], 2),
    ("composite_sentiment", ["cci", "business_barometer", "epu"], 2),
]

# percent weights; renormalised over whatever can actually be scored
WEIGHTS = {
    "cpi": 20 / 3, "gdp_growth": 20 / 3, "public_debt": 20 / 3,
    "bank_rate": 20 / 3, "ftse_volatility": 20 / 3, "gbp_fx_volatility": 20 / 3,
    "unemployment": 7.5, "job_security": 7.5,
    "composite_sentiment": 25,
    "purchasing_power": 20 / 3, }


def oriented_z(key: str, series: Series, as_of: datetime) -> float:
    min_observations = 16 if key == "gdp_growth" else 24
    z = trailing_zscore(
        series,
        as_of,
        min_observations=min_observations,
    )
    return -z if INDICATOR_DIRECTIONS[key] == "invert" else z


def blend(raw: dict, keys: list, as_of: datetime, min_parts: int):
    scores, problems = {}, {}
    for key in keys:
        try:
            scores[key] = oriented_z(key, raw[key], as_of)
        except ValueError as exc:
            problems[key] = str(exc)
    if len(scores) < min_parts:
        raise ValueError(f"only {len(scores)}/{len(keys)} components scorable: {problems}")
    return sum(scores.values()) / len(scores), sorted(scores)


# ------------------------------------------------------------
# Aggregation
# ------------------------------------------------------------

def compute_ukpi(raw: dict, as_of: datetime = None) -> dict:
    """as_of=None -> live mode (reference month found automatically).
    as_of=<date> -> score everything using only data on or before that date."""
    group_a = {k: v for k, v in raw.items() if k not in GROUP_B}
    reference_month = as_of or find_reference_month(group_a)
    group_b_cutoff = as_of or datetime.now()

    scores, excluded, components_used = {}, {}, {}

    for key in SIMPLE_GROUP_A:
        try:
            scores[key] = oriented_z(key, raw[key], reference_month)
        except ValueError as exc:
            excluded[key] = str(exc)

    for key in sorted(GROUP_B):
        try:
            scores[key] = oriented_z(key, raw[key], group_b_cutoff)
        except ValueError as exc:
            excluded[key] = str(exc)

    for name, parts, min_parts in COMPOSITES:
        try:
            scores[name], components_used[name] = blend(raw, parts, reference_month, min_parts)
        except ValueError as exc:
            excluded[name] = str(exc)

    if not scores:
        raise ValueError("No indicator could be scored")

    # Renormalise weights across indicators that can be scored.
    # Report original-weight coverage separately so missing data stays visible.
    total_weight = sum(WEIGHTS.values())
    weight_coverage = 100 * sum(WEIGHTS[k] for k in scores) / total_weight
    weights_used = {k: WEIGHTS[k] / sum(WEIGHTS[j] for j in scores) for k in scores}
    weighted_sum = sum(scores[k] * weights_used[k] for k in scores)

    return {
        "ukpi": weighted_sum * UKPI_SCALE,
        "reference_month": reference_month,
        "component_scores": scores,
        "weights_used": weights_used,
        "weight_coverage_pct": weight_coverage,
        "components_used": components_used,
        "excluded": excluded,
    }


def write_json_output(result: dict) -> None:
    output = {
        "ukpi": round(result["ukpi"], 3),
        "reference_month": result["reference_month"].strftime("%Y-%m"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "component_scores": {k: round(v, 3) for k, v in result["component_scores"].items()},
        "weights_used": {k: round(v, 4) for k, v in result["weights_used"].items()},
        "components_used": result["components_used"],
        "excluded": result["excluded"],
    }
    with open("data/ukpi_output.json", "w") as f:
        json.dump(output, f, indent=2)


if __name__ == "__main__":
    raw = gather_raw_data()
    result = compute_ukpi(raw)
    write_json_output(result)

    print(f"\n{'=' * 50}")
    print(f"UK PANIC INDEX (UKPI): {result['ukpi']:+.2f}")
    print(f"Reference month (Group A): {result['reference_month'].strftime('%Y-%m')}")
    print(f"Scored {len(result['component_scores'])} indicators")
    print(f"{'=' * 50}\n")
    print("Component z-scores (higher = more panic):")
    for key, score in result["component_scores"].items():
        print(f"  {key}: {score:+.3f}  (weight {result['weights_used'][key]:.1%})")
    if result["excluded"]:
        print("\nExcluded (insufficient history):")
        for key, reason in result["excluded"].items():
            print(f"  {key}: {reason[:90]}")
