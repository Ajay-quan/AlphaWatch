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
