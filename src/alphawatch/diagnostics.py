from __future__ import annotations

from math import sqrt

import numpy as np


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
