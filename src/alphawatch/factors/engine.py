from __future__ import annotations

from datetime import datetime

import polars as pl

from alphawatch.data.quality import enforce_frame_pit
from alphawatch.exceptions import DataContractError
from alphawatch.factors.cross_sectional import group_neutralize, percentile_rank, winsorize, zscore
from alphawatch.factors.fundamental import compute_fundamental_signals
from alphawatch.factors.market import market_signals

FUNDAMENTAL_FACTORS = ["size", "value", "profitability", "investment", "quality", "accrual_quality"]


def build_fundamental_factor_table(
    fundamentals: pl.DataFrame,
    prediction_time: datetime,
    sector_neutral: bool = True,
) -> pl.DataFrame:
    enforce_frame_pit(fundamentals, prediction_time)
    computed = compute_fundamental_signals(fundamentals, prediction_time)
    outputs: list[pl.DataFrame] = []
    for factor in FUNDAMENTAL_FACTORS:
        transformed = winsorize(computed, factor)
        if sector_neutral:
            if "sector" not in transformed.columns:
                raise DataContractError("sector is required for sector-neutral factors")
            transformed = group_neutralize(transformed, factor, "sector").with_columns(
                pl.col(f"{factor}_neutral").alias(factor)
            )
        transformed = percentile_rank(zscore(transformed, factor), factor)
        outputs.append(
            transformed.select(
                "security_id",
                pl.lit(prediction_time).alias("prediction_time"),
                pl.lit(factor).alias("factor_name"),
                pl.lit("1.0.0").alias("factor_version"),
                pl.col(factor).alias("standardized_value"),
                pl.col(f"{factor}_rank").alias("rank"),
                "available_at",
            )
        )
    return pl.concat(outputs)


def build_market_factor_table(
    market: pl.DataFrame, prediction_time: datetime, lookback: int = 60
) -> pl.DataFrame:
    enforce_frame_pit(market, prediction_time)
    signals = market_signals(market, lookback)
    latest = signals.sort("session").group_by("security_id", maintain_order=True).tail(1)
    frames = []
    for name in ("beta", "liquidity", "turnover_signal"):
        factor_name = "turnover" if name == "turnover_signal" else name
        frames.append(
            latest.select(
                "security_id",
                pl.lit(prediction_time).alias("prediction_time"),
                pl.lit(factor_name).alias("factor_name"),
                pl.lit("1.0.0").alias("factor_version"),
                pl.col(name).alias("raw_value"),
                "available_at",
            )
        )
    return pl.concat(frames)
