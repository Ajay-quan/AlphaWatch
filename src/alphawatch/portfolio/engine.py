from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum

import polars as pl

from alphawatch.portfolio.costs import LinearQuadraticCostModel


class Weighting(StrEnum):
    EQUAL = "equal"
    VALUE = "value"
    VOLATILITY = "volatility"
    RANK = "rank"


def _number(value: object, field: str) -> float:
    if not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    return float(value)


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    weighting: Weighting = Weighting.EQUAL
    quantile: float = 0.2
    holding_periods: int = 1
    rebalance_every: int = 1
    aum: float = 10_000_000.0
    max_adv_participation: float = 0.01
    max_absolute_weight: float = 0.05

    def __post_init__(self) -> None:
        if not 0 < self.quantile <= 0.5:
            raise ValueError("quantile must be in (0, 0.5]")
        if self.holding_periods < 1 or self.rebalance_every < 1 or self.aum <= 0:
            raise ValueError("holding_periods, rebalance_every and aum must be positive")
        if not 0 < self.max_adv_participation <= 1 or not 0 < self.max_absolute_weight <= 0.5:
            raise ValueError("invalid liquidity or position constraint")


def _side_weights(rows: list[dict[str, object]], weighting: Weighting) -> dict[str, float]:
    if weighting == Weighting.EQUAL:
        scores = [1.0] * len(rows)
    elif weighting == Weighting.VALUE:
        scores = [_number(row["market_cap"], "market_cap") for row in rows]
    elif weighting == Weighting.VOLATILITY:
        scores = [1.0 / _number(row["volatility"], "volatility") for row in rows]
    else:
        scores = [float(index + 1) for index in range(len(rows))]
    denominator = sum(scores)
    return {
        str(row["security_id"]): score / denominator
        for row, score in zip(rows, scores, strict=True)
    }


def _allocate_with_caps(
    desired: dict[str, float], capacities: dict[str, float], budget: float = 0.5
) -> dict[str, float]:
    """Proportionally allocate a side, redistributing weight until caps bind."""
    result = {name: 0.0 for name in desired}
    active = set(desired)
    remaining = min(budget, sum(capacities.values()))
    while active and remaining > 1e-15:
        score_total = sum(desired[name] for name in active)
        if score_total <= 0:
            break
        additions = {
            name: min(
                remaining * desired[name] / score_total,
                capacities[name] - result[name],
            )
            for name in active
        }
        allocated = sum(max(value, 0.0) for value in additions.values())
        if allocated <= 1e-15:
            break
        for name, value in additions.items():
            result[name] += max(value, 0.0)
        remaining -= allocated
        active = {
            name for name in active if capacities[name] - result[name] > 1e-15
        }
    return result


def construct_target(rows: list[dict[str, object]], config: PortfolioConfig) -> dict[str, float]:
    usable = [
        row
        for row in rows
        if row.get("signal") is not None
        and _number(row.get("average_dollar_volume", 0), "average_dollar_volume") > 0
        and (
            config.weighting != Weighting.VALUE
            or _number(row.get("market_cap", 0), "market_cap") > 0
        )
        and (
            config.weighting != Weighting.VOLATILITY
            or _number(row.get("volatility", 0), "volatility") > 0
        )
    ]
    usable.sort(key=lambda row: (_number(row["signal"], "signal"), str(row["security_id"])))
    count = min(max(1, int(len(usable) * config.quantile)), len(usable) // 2)
    if count == 0:
        return {}
    short_rows, long_rows = usable[:count], usable[-count:]
    result: dict[str, float] = {}
    for side_rows, sign in ((short_rows, -1.0), (long_rows, 1.0)):
        weighted_rows = (
            list(reversed(side_rows))
            if config.weighting == Weighting.RANK and sign < 0
            else side_rows
        )
        base = _side_weights(weighted_rows, config.weighting)
        capacities = {
            str(row["security_id"]): min(
                config.max_absolute_weight,
                _number(row["average_dollar_volume"], "average_dollar_volume")
                * config.max_adv_participation
                / config.aum,
            )
            for row in side_rows
        }
        allocated = _allocate_with_caps(base, capacities)
        result.update({security: sign * weight for security, weight in allocated.items()})
    return result


def run_portfolio(
    observations: pl.DataFrame,
    config: PortfolioConfig,
    costs: LinearQuadraticCostModel,
) -> tuple[pl.DataFrame, pl.DataFrame]:
    required = {"date", "security_id", "signal", "return", "average_dollar_volume"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"portfolio input missing: {sorted(missing)}")
    records = observations.sort(["date", "security_id"]).to_dicts()
    grouped: dict[date, list[dict[str, object]]] = {}
    for row in records:
        period_value = row["date"]
        if isinstance(period_value, datetime):
            period = period_value.date()
        elif isinstance(period_value, date):
            period = period_value
        else:
            raise ValueError("date must contain date or datetime values")
        grouped.setdefault(period, []).append(row)
    cohorts: list[dict[str, float]] = []
    previous: dict[str, float] = {}
    last_adv: dict[str, float] = {}
    weight_rows: list[dict[str, object]] = []
    return_rows: list[dict[str, object]] = []
    for period_index, period in enumerate(sorted(grouped)):
        if period_index % config.rebalance_every == 0:
            cohort = construct_target(grouped[period], config)
            cohorts.append(cohort)
            cohorts = cohorts[-config.holding_periods :]
            names = set().union(*(set(item) for item in cohorts))
            target = {
                name: sum(item.get(name, 0.0) for item in cohorts) / len(cohorts)
                for name in names
            }
        else:
            target = previous.copy()
        all_names = set(previous) | set(target)
        trades = {
            name: target.get(name, 0.0) - previous.get(name, 0.0)
            for name in all_names
        }
        one_way_turnover = 0.5 * sum(abs(value) for value in trades.values())
        returns = {
            str(row["security_id"]): _number(row["return"], "return")
            for row in grouped[period]
        }
        adv = {
            str(row["security_id"]): _number(
                row["average_dollar_volume"], "average_dollar_volume"
            )
            for row in grouped[period]
        }
        last_adv.update(adv)
        missing_returns = set(target) - set(returns)
        if missing_returns:
            raise ValueError(
                "active securities require an explicit return or terminal outcome: "
                f"{sorted(missing_returns)}"
            )
        gross = sum(weight * returns.get(name, 0.0) for name, weight in target.items())
        cost = costs.estimate_trades(trades, last_adv, config.aum)
        return_rows.append(
            {
                "date": period,
                "gross_return": gross,
                "turnover": one_way_turnover,
                "cost": cost,
                "net_return": gross - cost,
            }
        )
        for name in sorted(all_names):
            weight_rows.append(
                {
                    "date": period,
                    "security_id": name,
                    "previous_weight": previous.get(name, 0.0),
                    "weight": target.get(name, 0.0),
                    "trade_weight": trades[name],
                }
            )
        previous = target
    return pl.DataFrame(weight_rows), pl.DataFrame(return_rows)
