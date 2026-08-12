from __future__ import annotations

from dataclasses import dataclass

import polars as pl

from alphawatch.portfolio.costs import LinearQuadraticCostModel


@dataclass(frozen=True, slots=True)
class BacktestResult:
    weights: pl.DataFrame
    returns: pl.DataFrame


def long_short_backtest(
    observations: pl.DataFrame,
    cost_model: LinearQuadraticCostModel,
    quantile: float = 0.2,
) -> BacktestResult:
    required = {"date", "security_id", "signal", "forward_return"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"backtest input missing columns: {sorted(missing)}")
    if not 0 < quantile <= 0.5:
        raise ValueError("quantile must be in (0, 0.5]")
    ranked = observations.drop_nulls(["signal", "forward_return"]).with_columns(
        pl.col("signal").rank("average").over("date").alias("rank"),
        pl.len().over("date").alias("count"),
    )
    tail = ranked.with_columns(
        pl.when(pl.col("rank") <= (pl.col("count") * quantile).floor().clip(lower_bound=1))
        .then(-1.0)
        .when(
            pl.col("rank")
            > pl.col("count") - (pl.col("count") * quantile).floor().clip(lower_bound=1)
        )
        .then(1.0)
        .otherwise(0.0)
        .alias("side")
    ).filter(pl.col("side") != 0)
    weights = tail.with_columns(
        (pl.col("side") * 0.5 / pl.len().over(["date", "side"])).alias("weight")
    ).sort(["security_id", "date"])
    weights = weights.with_columns(
        pl.col("weight").shift(1).over("security_id").fill_null(0.0).alias("previous_weight")
    )
    daily = (
        weights.group_by("date")
        .agg(
            (pl.col("weight") * pl.col("forward_return")).sum().alias("gross_return"),
            (0.5 * (pl.col("weight") - pl.col("previous_weight")).abs().sum()).alias("turnover"),
        )
        .sort("date")
    )
    linear = cost_model.commission_bps + cost_model.half_spread_bps + cost_model.slippage_bps
    daily = daily.with_columns(
        (
            (linear * pl.col("turnover") + cost_model.quadratic_bps * pl.col("turnover") ** 2)
            / 10_000
        ).alias("cost")
    ).with_columns((pl.col("gross_return") - pl.col("cost")).alias("net_return"))
    return BacktestResult(weights, daily)
