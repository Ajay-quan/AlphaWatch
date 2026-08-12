import numpy as np
import pytest

from alphawatch.research.policy import simulate_decay_policy
from alphawatch.research.structural import negative_mean_cusum


def test_negative_cusum_detects_sustained_deterioration_after_reference_period() -> None:
    result = negative_mean_cusum([0.1, -0.1, 0.1, -0.1, -1.0, -1.0], training_window=4)
    assert result.event_indices.tolist() == [4, 5]
    assert result.threshold > 0
    assert result.statistic[:4].tolist() == [0.0] * 4


def test_cusum_rejects_constant_reference_window() -> None:
    with pytest.raises(ValueError, match="non-zero"):
        negative_mean_cusum([1.0, 1.0, 1.0, 0.0], training_window=3)


def test_decay_policy_lags_execution_and_charges_turnover_costs() -> None:
    result = simulate_decay_policy(
        [0.1, 0.1, 0.1], [0.1, 0.9, 0.1], threshold=0.5, reduced_exposure=0.5,
        cost_per_turnover=0.02,
    )
    assert result.exposures.tolist() == [1.0, 1.0, 0.5]
    assert result.gross_returns.tolist() == pytest.approx([0.1, 0.1, 0.05])
    assert result.turnover.tolist() == pytest.approx([0.0, 0.0, 0.25])
    assert result.net_returns[-1] == pytest.approx(0.045)
    assert np.isfinite(result.total_cost)
