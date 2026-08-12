from __future__ import annotations

import polars as pl


def winsorize(
    frame: pl.DataFrame, column: str, lower: float = 0.01, upper: float = 0.99
) -> pl.DataFrame:
    if not 0 <= lower < upper <= 1:
        raise ValueError("quantiles must satisfy 0 <= lower < upper <= 1")
    return frame.with_columns(
        pl.col(column)
        .clip(pl.col(column).quantile(lower), pl.col(column).quantile(upper))
        .alias(column)
    )


def zscore(frame: pl.DataFrame, column: str, by: list[str] | None = None) -> pl.DataFrame:
    value = pl.col(column)
    mean = value.mean().over(by) if by else value.mean()
    std = value.std(ddof=1).over(by) if by else value.std(ddof=1)
    return frame.with_columns(
        pl.when(std.is_not_null() & (std > 0))
        .then((value - mean) / std)
        .otherwise(None)
        .alias(column)
    )


def percentile_rank(frame: pl.DataFrame, column: str) -> pl.DataFrame:
    count = pl.col(column).count()
    return frame.with_columns(
        pl.when(count > 1)
        .then((pl.col(column).rank("average") - 1) / (count - 1))
        .otherwise(0.5)
        .alias(f"{column}_rank")
    )


def neutralize(frame: pl.DataFrame, column: str, controls: list[str]) -> pl.DataFrame:
    """OLS residualize a signal on numeric controls plus intercept."""
    import numpy as np

    clean = frame.drop_nulls([column, *controls])
    if clean.height <= len(controls) + 1:
        return frame.with_columns(pl.lit(None, dtype=pl.Float64).alias(f"{column}_neutral"))
    y = clean[column].to_numpy()
    x = np.column_stack([np.ones(clean.height), *[clean[c].to_numpy() for c in controls]])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    residuals = y - x @ beta
    residual_frame = clean.select("security_id").with_columns(
        pl.Series(f"{column}_neutral", residuals)
    )
    return frame.join(residual_frame, on="security_id", how="left")


def group_neutralize(frame: pl.DataFrame, column: str, group: str) -> pl.DataFrame:
    """Remove contemporaneous categorical group means, e.g. sector effects."""
    if group not in frame.columns:
        raise ValueError(f"missing neutralization group: {group}")
    return frame.with_columns(
        (pl.col(column) - pl.col(column).mean().over(group)).alias(f"{column}_neutral")
    )
