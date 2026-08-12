from __future__ import annotations

import polars as pl

from alphawatch.exceptions import DataContractError


def compute_fundamental_signals(frame: pl.DataFrame) -> pl.DataFrame:
    """Transparent raw signals; input must already be an as-of-safe snapshot."""
    required = {
        "security_id",
        "available_at",
        "market_cap",
        "book_equity",
        "operating_profit",
        "total_assets",
        "total_assets_lag",
        "accruals",
        "cash_flow_operations",
    }
    missing = required - set(frame.columns)
    if missing:
        raise DataContractError(f"fundamental schema missing columns: {sorted(missing)}")
    return frame.with_columns(
        (-pl.col("market_cap").log()).alias("size"),
        (pl.col("book_equity") / pl.col("market_cap")).alias("value"),
        (pl.col("operating_profit") / pl.col("book_equity")).alias("profitability"),
        (-(pl.col("total_assets") / pl.col("total_assets_lag") - 1)).alias("investment"),
        (
            pl.col("cash_flow_operations") / pl.col("total_assets")
            - pl.col("accruals").abs() / pl.col("total_assets")
        ).alias("quality"),
        (-pl.col("accruals") / pl.col("total_assets")).alias("accrual_quality"),
    )
