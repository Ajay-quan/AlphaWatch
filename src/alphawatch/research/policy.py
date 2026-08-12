"""Cost-aware historical simulations for frozen factor-health policies."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class PolicySimulation:
    """Return path and exposures from a rule chosen outside its evaluation period."""

    gross_returns: np.ndarray
    net_returns: np.ndarray
    exposures: np.ndarray
    turnover: np.ndarray
    total_cost: float


def simulate_decay_policy(
    factor_returns: Sequence[float],
    decay_probabilities: Sequence[float],
    threshold: float,
    reduced_exposure: float,
    cost_per_turnover: float,
    execution_lag: int = 1,
) -> PolicySimulation:
    """Apply a preselected probability threshold with one-way turnover costs.

    Signals at ``t`` change exposure only after ``execution_lag`` periods. This
    prevents a same-period signal/return assumption from overstating performance.
    """
    returns = np.asarray(factor_returns, dtype=float)
    probabilities = np.asarray(decay_probabilities, dtype=float)
    if returns.ndim != 1 or probabilities.ndim != 1 or len(returns) != len(probabilities):
        raise ValueError(
            "returns and probabilities must be equally sized one-dimensional sequences"
        )
    if not len(returns) or not np.isfinite(returns).all() or not np.isfinite(probabilities).all():
        raise ValueError("inputs must be non-empty and finite")
    if not 0 <= threshold <= 1 or not 0 <= reduced_exposure <= 1 or cost_per_turnover < 0:
        raise ValueError("invalid threshold, reduced_exposure, or cost_per_turnover")
    if execution_lag < 1:
        raise ValueError("execution_lag must be at least one period")
    target_exposure = np.where(probabilities >= threshold, reduced_exposure, 1.0)
    exposures = np.ones(len(returns), dtype=float)
    if execution_lag < len(returns):
        exposures[execution_lag:] = target_exposure[:-execution_lag]
    turnover = 0.5 * np.abs(np.diff(exposures, prepend=1.0))
    gross = exposures * returns
    costs = turnover * cost_per_turnover
    return PolicySimulation(gross, gross - costs, exposures, turnover, float(costs.sum()))
