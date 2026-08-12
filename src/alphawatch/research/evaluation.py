"""Out-of-sample classification evaluation for factor-decay warnings.

All functions take labels and predictions in their original chronological order.
They deliberately do not select thresholds from the final test data.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True, slots=True)
class ClassificationMetrics:
    """Discrimination, threshold, and probability-quality metrics."""

    prevalence: float
    pr_auc: float
    roc_auc: float
    brier_score: float
    precision: float
    recall: float
    f1: float
    threshold: float


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    """Observed event frequency for a fixed predicted-probability bin."""

    lower: float
    upper: float
    count: int
    mean_prediction: float
    observed_frequency: float


def classification_metrics(
    labels: Sequence[bool | int], probabilities: Sequence[float], threshold: float
) -> ClassificationMetrics:
    """Calculate test metrics for a threshold chosen before final-test access."""
    y_true, y_score = _validate(labels, probabilities)
    if not 0 <= threshold <= 1:
        raise ValueError("threshold must be in [0, 1]")
    predicted = y_score >= threshold
    true_positive = int(np.sum(predicted & y_true))
    false_positive = int(np.sum(predicted & ~y_true))
    false_negative = int(np.sum(~predicted & y_true))
    predicted_positive = true_positive + false_positive
    actual_positive = true_positive + false_negative
    precision = true_positive / predicted_positive if predicted_positive else 0.0
    recall = true_positive / actual_positive if actual_positive else 0.0
    return ClassificationMetrics(
        prevalence=float(y_true.mean()),
        pr_auc=_average_precision(y_true, y_score),
        roc_auc=_roc_auc(y_true, y_score),
        brier_score=float(np.mean((y_score - y_true.astype(float)) ** 2)),
        precision=precision,
        recall=recall,
        f1=2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        threshold=threshold,
    )


def calibration_bins(
    labels: Sequence[bool | int], probabilities: Sequence[float], n_bins: int = 10
) -> list[CalibrationBin]:
    """Return fixed-width calibration bins, retaining empty bins for auditability."""
    y_true, y_score = _validate(labels, probabilities)
    if n_bins < 2:
        raise ValueError("n_bins must be at least 2")
    result: list[CalibrationBin] = []
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    for index, (lower, upper) in enumerate(zip(edges[:-1], edges[1:], strict=True)):
        members = (y_score >= lower) & (y_score < upper if index < n_bins - 1 else y_score <= upper)
        count = int(members.sum())
        result.append(
            CalibrationBin(
                float(lower),
                float(upper),
                count,
                float(y_score[members].mean()) if count else float("nan"),
                float(y_true[members].mean()) if count else float("nan"),
            )
        )
    return result


def benjamini_hochberg(p_values: Sequence[float]) -> np.ndarray:
    """Return FDR-adjusted p-values in the original hypothesis order."""
    values = np.asarray(p_values, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all():
        raise ValueError("p_values must be a non-empty, finite one-dimensional sequence")
    if np.any((values < 0) | (values > 1)):
        raise ValueError("p_values must be in [0, 1]")
    order = np.argsort(values)
    ranked = values[order] * len(values) / np.arange(1, len(values) + 1)
    adjusted_sorted = np.minimum.accumulate(ranked[::-1])[::-1]
    adjusted = np.empty_like(values)
    adjusted[order] = np.minimum(adjusted_sorted, 1.0)
    return adjusted


def paired_moving_block_difference_ci(
    full_scores: Sequence[float],
    baseline_scores: Sequence[float],
    block_length: int = 21,
    confidence: float = 0.95,
    n_resamples: int = 2_000,
    seed: int = 0,
) -> tuple[float, float, float]:
    """Estimate the paired mean score improvement with dependent blocks preserved."""
    full, baseline = _finite_equal_vectors(full_scores, baseline_scores)
    if not 1 <= block_length <= len(full):
        raise ValueError("block_length must be between 1 and the number of scores")
    if not 0 < confidence < 1 or n_resamples < 1:
        raise ValueError("confidence must be in (0, 1) and n_resamples positive")
    difference = full - baseline
    generator = np.random.default_rng(seed)
    n = len(difference)
    n_blocks = int(np.ceil(n / block_length))
    starts = generator.integers(0, n - block_length + 1, size=(n_resamples, n_blocks))
    samples = difference[starts[:, :, None] + np.arange(block_length)]
    samples = samples.reshape(n_resamples, -1)[:, :n]
    alpha = (1 - confidence) / 2
    estimates = samples.mean(axis=1)
    return (
        float(difference.mean()),
        float(np.quantile(estimates, alpha)),
        float(np.quantile(estimates, 1 - alpha)),
    )


def circular_shift_placebo(probabilities: Sequence[float], shift: int) -> np.ndarray:
    """Break date alignment without destroying the score distribution."""
    values = np.asarray(probabilities, dtype=float)
    if values.ndim != 1 or len(values) < 2 or not np.isfinite(values).all():
        raise ValueError("probabilities must contain at least two finite values")
    if shift % len(values) == 0:
        raise ValueError("shift must not be a multiple of the sequence length")
    return np.roll(values, shift)


def _validate(
    labels: Sequence[bool | int], probabilities: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    y_score = np.asarray(probabilities, dtype=float)
    y_raw = np.asarray(labels)
    if y_raw.ndim != 1 or y_score.ndim != 1 or len(y_raw) != len(y_score) or len(y_raw) < 2:
        raise ValueError("labels and probabilities must be equally sized one-dimensional sequences")
    if not np.isfinite(y_score).all() or np.any((y_score < 0) | (y_score > 1)):
        raise ValueError("probabilities must be finite and in [0, 1]")
    if not np.isin(y_raw, [False, True, 0, 1]).all():
        raise ValueError("labels must be binary")
    y_true = y_raw.astype(bool)
    if not y_true.any() or y_true.all():
        raise ValueError("both label classes are required for ranking metrics")
    return y_true, y_score


def _finite_equal_vectors(
    left: Sequence[float], right: Sequence[float]
) -> tuple[np.ndarray, np.ndarray]:
    first, second = np.asarray(left, dtype=float), np.asarray(right, dtype=float)
    if first.ndim != 1 or second.ndim != 1 or len(first) != len(second) or len(first) < 2:
        raise ValueError("inputs must be equally sized one-dimensional sequences")
    if not np.isfinite(first).all() or not np.isfinite(second).all():
        raise ValueError("inputs must be finite")
    return first, second


def _average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    order = np.argsort(-y_score, kind="stable")
    sorted_labels = y_true[order]
    cumulative_true = np.cumsum(sorted_labels)
    precision = cumulative_true / np.arange(1, len(sorted_labels) + 1)
    return float(precision[sorted_labels].sum() / sorted_labels.sum())


def _roc_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    positive, negative = y_score[y_true], y_score[~y_true]
    comparisons = (positive[:, None] > negative).mean()
    comparisons += 0.5 * (positive[:, None] == negative).mean()
    return float(comparisons)
