from __future__ import annotations

from math import sqrt

import numpy as np
import polars as pl


def performance_metrics(returns: list[float], annualization: int = 252) -> dict[str, float]:
    if not returns:
        raise ValueError("returns cannot be empty")
    values = np.asarray(returns, dtype=float)
    wealth = np.cumprod(1 + values)
    peaks = np.maximum.accumulate(wealth)
    drawdowns = wealth / peaks - 1
    years = len(values) / annualization
    cagr = float(wealth[-1] ** (1 / years) - 1) if years > 0 and wealth[-1] > 0 else -1.0
    vol = float(values.std(ddof=1) * sqrt(annualization)) if len(values) > 1 else 0.0
    mean_ann = float(values.mean() * annualization)
    downside = values[values < 0]
    downside_vol = float(downside.std(ddof=1) * sqrt(annualization)) if len(downside) > 1 else 0.0
    max_drawdown = float(drawdowns.min())
    return {
        "cagr": cagr,
        "annualized_volatility": vol,
        "sharpe": mean_ann / vol if vol else 0.0,
        "sortino": mean_ann / downside_vol if downside_vol else 0.0,
        "maximum_drawdown": max_drawdown,
        "calmar": cagr / abs(max_drawdown) if max_drawdown else 0.0,
        "skewness": float(((values - values.mean()) ** 3).mean() / values.std() ** 3)
        if values.std()
        else 0.0,
        "excess_kurtosis": float(((values - values.mean()) ** 4).mean() / values.var() ** 2 - 3)
        if values.var()
        else 0.0,
        "var_95": float(np.quantile(values, 0.05)),
        "cvar_95": float(values[values <= np.quantile(values, 0.05)].mean()),
    }


def information_coefficient(
    signal: list[float], forward_return: list[float], rank: bool = True
) -> float:
    if len(signal) != len(forward_return) or len(signal) < 2:
        raise ValueError("equal vectors with at least two observations are required")
    left, right = np.asarray(signal), np.asarray(forward_return)
    if rank:
        left = np.argsort(np.argsort(left)).astype(float)
        right = np.argsort(np.argsort(right)).astype(float)
    result = np.corrcoef(left, right)[0, 1]
    return float(result)


def exposure_diagnostics(
    weights: list[float], beta: list[float], size: list[float], liquidity: list[float]
) -> dict[str, float]:
    lengths = {len(weights), len(beta), len(size), len(liquidity)}
    if len(lengths) != 1 or not weights:
        raise ValueError("equal, non-empty exposure vectors are required")
    w = np.asarray(weights, dtype=float)
    return {
        "net_exposure": float(w.sum()),
        "gross_exposure": float(np.abs(w).sum()),
        "beta_exposure": float(w @ np.asarray(beta, dtype=float)),
        "size_exposure": float(w @ np.asarray(size, dtype=float)),
        "liquidity_exposure": float(w @ np.asarray(liquidity, dtype=float)),
        "largest_absolute_weight": float(np.abs(w).max()),
    }


def rolling_metrics(
    returns: list[float], window: int, annualization: int = 252
) -> list[dict[str, float]]:
    if window < 2:
        raise ValueError("window must be at least two")
    if len(returns) < window:
        return []
    return [
        performance_metrics(returns[end - window : end], annualization)
        for end in range(window, len(returns) + 1)
    ]


def factor_diagnostics(
    observations: pl.DataFrame, quantiles: int = 5
) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Produce dated ICs and aggregate IC/quantile-monotonicity diagnostics."""
    required = {"date", "factor_name", "signal", "forward_return"}
    missing = required - set(observations.columns)
    if missing:
        raise ValueError(f"diagnostic input missing: {sorted(missing)}")
    if quantiles < 2:
        raise ValueError("quantiles must be at least two")
    detail: list[dict[str, object]] = []
    summary: list[dict[str, object]] = []
    for factor_frame in observations.partition_by("factor_name", maintain_order=True):
        factor = str(factor_frame["factor_name"][0])
        factor_ics: list[float] = []
        bucket_returns: dict[int, list[float]] = {bucket: [] for bucket in range(quantiles)}
        for dated in factor_frame.partition_by("date", maintain_order=True):
            clean = dated.drop_nulls(["signal", "forward_return"]).sort("signal")
            if clean.height < 2:
                continue
            ic = information_coefficient(
                clean["signal"].to_list(), clean["forward_return"].to_list()
            )
            factor_ics.append(ic)
            buckets = np.floor(np.arange(clean.height) * quantiles / clean.height).astype(int)
            for bucket, value in zip(buckets, clean["forward_return"], strict=True):
                bucket_returns[int(bucket)].append(float(value))
            detail.append(
                {"date": clean["date"][0], "factor_name": factor, "information_coefficient": ic}
            )
        means = [
            float(np.mean(bucket_returns[index])) if bucket_returns[index] else np.nan
            for index in range(quantiles)
        ]
        monotonicity = (
            information_coefficient(list(range(quantiles)), means, rank=False)
            if not any(np.isnan(means))
            else float("nan")
        )
        ic_mean = float(np.mean(factor_ics)) if factor_ics else float("nan")
        ic_std = float(np.std(factor_ics, ddof=1)) if len(factor_ics) > 1 else float("nan")
        summary.append(
            {
                "factor_name": factor,
                "observations": len(factor_ics),
                "ic_mean": ic_mean,
                "ic_information_ratio": ic_mean / ic_std if ic_std > 0 else float("nan"),
                "quantile_monotonicity": monotonicity,
                **{f"q{index + 1}_mean_return": value for index, value in enumerate(means)},
            }
        )
    return pl.DataFrame(detail), pl.DataFrame(summary)
