from datetime import date, timedelta

import numpy as np
import pytest

from alphawatch.research.validation import (
    PurgedWalkForwardSplit,
    moving_block_bootstrap_ci,
    rank_ic_deterioration_labels,
)


def test_rank_ic_label_starts_after_prediction_date() -> None:
    # The first eligible point has trailing mean 1.0 and a future mean -1.0.
    result = rank_ic_deterioration_labels(
        [1.0, 1.0, 1.0, -1.0, -1.0], horizon=2, trailing_window=3
    )
    assert result.valid.tolist() == [False, False, True, False, False]
    assert result.label.tolist() == [False, False, True, False, False]
    assert result.trailing_mean[2] == pytest.approx(1.0)
    assert result.forward_mean[2] == pytest.approx(-1.0)


def test_purged_folds_remove_overlapping_forward_labels_and_embargo() -> None:
    dates = [date(2020, 1, 1) + timedelta(days=index) for index in range(30)]
    splitter = PurgedWalkForwardSplit(
        n_splits=2, test_size=5, label_horizon=3, embargo=2, min_train_size=5
    )
    folds = splitter.split(dates)
    for fold in folds:
        assert fold.train_indices[-1] + 3 < fold.test_indices[0] - 2
        assert fold.train_indices[-1] < fold.test_indices[0]


def test_splitter_rejects_non_chronological_timestamps() -> None:
    with pytest.raises(ValueError, match="strictly increasing"):
        PurgedWalkForwardSplit(
            n_splits=1, test_size=2, label_horizon=1, min_train_size=2
        ).split(
            [date(2020, 1, 2), date(2020, 1, 1), date(2020, 1, 3), date(2020, 1, 4)]
        )


def test_moving_block_bootstrap_is_reproducible_and_contains_mean_for_constant_series() -> None:
    first = moving_block_bootstrap_ci(np.ones(30), block_length=5, n_resamples=200, seed=7)
    second = moving_block_bootstrap_ci(np.ones(30), block_length=5, n_resamples=200, seed=7)
    assert first == second == (1.0, 1.0, 1.0)
