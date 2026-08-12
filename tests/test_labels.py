from datetime import datetime, timedelta

from alphawatch.research.labels import (
    future_mean_deterioration,
    future_minimum_breach,
    future_rank_ic_deterioration,
    future_structural_break,
)


def test_forward_label_is_not_available_at_prediction_time() -> None:
    times = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(4)]
    labels = future_rank_ic_deterioration(
        times, [0.1, -0.1, -0.2, 0.2], horizon=2, deterioration_threshold=0
    )
    assert len(labels) == 2
    assert labels[0].value == 1.0
    assert labels[0].available_at == times[2]
    assert labels[0].available_at > labels[0].prediction_timestamp


def test_all_remaining_forward_target_families_are_resolved_at_horizon_end() -> None:
    times = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(4)]
    sharpe = future_mean_deterioration(times, [1.0, 0.2, -0.2, 0.1], 2, 0.0)
    drawdown = future_minimum_breach(times, [0.0, -0.03, -0.12, 0.0], 2, -0.10)
    breaks = future_structural_break(times, [False, False, True, False], 2)
    assert sharpe[0].value == 0.0
    assert drawdown[0].value == 1.0
    assert breaks[0].value == 1.0
    assert all(label.available_at == label.label_end for label in sharpe + drawdown + breaks)
