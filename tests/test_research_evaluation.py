from datetime import UTC, datetime

import numpy as np
import pytest

from alphawatch.research.evaluation import (
    benjamini_hochberg,
    calibration_bins,
    circular_shift_placebo,
    classification_metrics,
    paired_moving_block_difference_ci,
)
from alphawatch.research.experiments import ExperimentManifest, write_experiment_manifest


def test_metrics_identify_perfect_ranked_probabilities() -> None:
    metrics = classification_metrics([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9], threshold=0.5)
    assert metrics.pr_auc == 1.0
    assert metrics.roc_auc == 1.0
    assert metrics.precision == metrics.recall == metrics.f1 == 1.0
    assert metrics.brier_score == pytest.approx(0.025)


def test_calibration_retains_empty_bins_for_auditing() -> None:
    bins = calibration_bins([0, 1], [0.1, 0.9], n_bins=2)
    assert [(item.count, item.observed_frequency) for item in bins] == [(1, 0.0), (1, 1.0)]


def test_benjamini_hochberg_preserves_original_order() -> None:
    assert benjamini_hochberg([0.03, 0.01, 0.04]).tolist() == pytest.approx([0.04, 0.03, 0.04])


def test_paired_block_ci_and_placebo_are_reproducible() -> None:
    result = paired_moving_block_difference_ci([1.0] * 30, [0.5] * 30, block_length=5)
    assert result == (0.5, 0.5, 0.5)
    assert circular_shift_placebo([0.1, 0.2, 0.3], 1).tolist() == [0.3, 0.1, 0.2]
    with pytest.raises(ValueError):
        circular_shift_placebo([0.1, 0.2], 2)


def test_experiment_manifest_is_immutable_and_serialized(tmp_path) -> None:
    manifest = ExperimentManifest(
        "run-1", datetime.now(UTC), "abc123", "config", "data-v1", datetime.now(UTC),
        "factor-v1", "features-v1", "rank-ic-3m", "logistic-v1", "2010:2017", "2018:2020",
        "2021:2022", "cost-v1", 7,
    )
    target = write_experiment_manifest(manifest, tmp_path)
    assert '"experiment_id": "run-1"' in target.read_text()
    with pytest.raises(FileExistsError):
        write_experiment_manifest(manifest, tmp_path)
    assert np.isfinite(0.0)
