from __future__ import annotations

import polars as pl

from alphawatch.exceptions import DataContractError


def eligible_universe(
    frame: pl.DataFrame,
    minimum_price: float = 5.0,
    minimum_dollar_volume: float = 1_000_000.0,
) -> pl.DataFrame:
    required = {"security_id", "session", "adjusted_close", "dollar_volume", "share_class"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"universe schema missing: {sorted(missing)}")
    return frame.filter(
        (pl.col("share_class") == "common")
        & (pl.col("adjusted_close") >= minimum_price)
        & (pl.col("dollar_volume") >= minimum_dollar_volume)
    )


def rolling_universe(
    frame: pl.DataFrame,
    minimum_price: float = 5.0,
    minimum_median_dollar_volume: float = 1_000_000.0,
    liquidity_window: int = 60,
    minimum_history: int = 252,
) -> pl.DataFrame:
    """Point-in-time eligibility using trailing observations only."""
    required = {"security_id", "session", "adjusted_close", "dollar_volume", "share_class"}
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"universe schema missing: {sorted(missing)}")
    ordered = frame.sort(["security_id", "session"])
    return ordered.with_columns(
        pl.col("dollar_volume")
        .rolling_median(liquidity_window, min_samples=liquidity_window)
        .over("security_id")
        .alias("median_dollar_volume"),
        pl.col("session").cum_count().over("security_id").alias("history_observations"),
    ).with_columns(
        (
            (pl.col("share_class") == "common")
            & (pl.col("adjusted_close") >= minimum_price)
            & (pl.col("median_dollar_volume") >= minimum_median_dollar_volume)
            & (pl.col("history_observations") >= minimum_history)
        ).alias("eligible")
    )
