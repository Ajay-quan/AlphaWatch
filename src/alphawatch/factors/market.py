from __future__ import annotations

import polars as pl

from alphawatch.exceptions import DataContractError


def market_signals(frame: pl.DataFrame, lookback: int = 60) -> pl.DataFrame:
    required = {"security_id", "session", "return", "market_return", "dollar_volume", "turnover"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"market signal schema missing: {sorted(missing)}")
    ordered = frame.sort(["security_id", "session"])
    min_periods = max(20, lookback // 2)
    cov = pl.rolling_cov(
        "return", "market_return", window_size=lookback, min_samples=min_periods
    ).over("security_id")
    market_var = (
        pl.col("market_return").rolling_var(lookback, min_samples=min_periods).over("security_id")
    )
    return ordered.with_columns(
        (cov / market_var).alias("beta"),
        pl.col("dollar_volume")
        .log()
        .rolling_mean(lookback, min_samples=min_periods)
        .over("security_id")
        .alias("liquidity"),
        pl.col("turnover")
        .rolling_mean(lookback, min_samples=min_periods)
        .over("security_id")
        .alias("turnover_signal"),
    )
