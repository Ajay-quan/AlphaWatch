from datetime import datetime, timedelta

from alphawatch.research.validation import chronological_purged_folds


def test_purged_folds_remove_overlapping_forward_labels() -> None:
    times = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(12)]
    # A four-day forward target: a training label must finish before validation starts.
    ends = [time + timedelta(days=4) for time in times]
    folds = chronological_purged_folds(times, ends, n_splits=2, embargo_observations=1, min_train_size=1)
    for fold in folds:
        for idx in fold.train_indices:
            assert ends[idx] < fold.validation_start
        assert max(fold.train_indices) < min(fold.validation_indices) - 1


def test_rolling_window_caps_the_chronological_training_history() -> None:
    times = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(20)]
    ends = [time + timedelta(days=1) for time in times]
    folds = chronological_purged_folds(
        times, ends, n_splits=2, min_train_size=3, training_window_observations=4
    )
    assert all(len(fold.train_indices) <= 4 for fold in folds)
    assert all(max(fold.train_indices) < min(fold.validation_indices) for fold in folds)
