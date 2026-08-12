"""Statistically defensible validation tools for factor-decay research."""

from alphawatch.research.validation import (
    DecayLabels,
    Fold,
    PurgedWalkForwardSplit,
    moving_block_bootstrap_ci,
    rank_ic_deterioration_labels,
)

__all__ = [
    "DecayLabels",
    "Fold",
    "PurgedWalkForwardSplit",
    "moving_block_bootstrap_ci",
    "rank_ic_deterioration_labels",
]
