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
