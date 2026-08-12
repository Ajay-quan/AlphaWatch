"""Small, dependency-light uncertainty and multiplicity controls."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .contracts import ResearchIntegrityError


@dataclass(frozen=True)
class ConfidenceInterval:
    estimate: float
    lower: float
    upper: float
    confidence: float


def moving_block_bootstrap_mean_ci(
    values: Sequence[float],
    block_size: int,
    n_resamples: int = 2_000,
    confidence: float = 0.95,
    seed: int = 0,
) -> ConfidenceInterval:
    """Percentile CI for a serially dependent mean using circular moving blocks."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 2 or not np.isfinite(x).all():
        raise ResearchIntegrityError("bootstrap input must be a finite one-dimensional series")
    if not 1 <= block_size <= len(x) or n_resamples < 100 or not 0 < confidence < 1:
        raise ResearchIntegrityError("invalid bootstrap settings")
    rng = np.random.default_rng(seed)
    n_blocks = int(np.ceil(len(x) / block_size))
    starts = rng.integers(0, len(x), size=(n_resamples, n_blocks))
    offsets = np.arange(block_size)
    samples = x[(starts[..., None] + offsets) % len(x)].reshape(n_resamples, -1)[:, : len(x)]
    means = samples.mean(axis=1)
    tail = (1 - confidence) / 2
    return ConfidenceInterval(
        float(x.mean()),
        float(np.quantile(means, tail)),
        float(np.quantile(means, 1 - tail)),
        confidence,
    )


@dataclass(frozen=True)
class MultipleTestingResult:
    hypothesis_id: str
    p_value: float
    adjusted_p_value: float
    rejected: bool


def benjamini_hochberg(
    p_values: dict[str, float], false_discovery_rate: float = 0.05
) -> list[MultipleTestingResult]:
    """Control false discovery rate across the declared family of hypotheses."""
    if not p_values or not 0 < false_discovery_rate < 1:
        raise ResearchIntegrityError("p-values and false discovery rate are required")
    if any(not 0 <= p <= 1 for p in p_values.values()):
        raise ResearchIntegrityError("p-values must be in [0, 1]")
    ordered = sorted(p_values.items(), key=lambda pair: pair[1])
    m = len(ordered)
    adjusted = [min(1.0, p * m / (rank + 1)) for rank, (_, p) in enumerate(ordered)]
    for i in range(m - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
    return [
        MultipleTestingResult(name, p, adjusted[rank], adjusted[rank] <= false_discovery_rate)
        for rank, (name, p) in enumerate(ordered)
    ]
