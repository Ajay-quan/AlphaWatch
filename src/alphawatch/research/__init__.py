"""Statistically defensible validation tools for factor-decay research."""

from alphawatch.research.evaluation import (
    CalibrationBin,
    ClassificationMetrics,
    benjamini_hochberg,
    calibration_bins,
    circular_shift_placebo,
    classification_metrics,
    paired_moving_block_difference_ci,
)
from alphawatch.research.experiments import ExperimentManifest, write_experiment_manifest
from alphawatch.research.validation import (
    DecayLabels,
    Fold,
    PurgedWalkForwardSplit,
    moving_block_bootstrap_ci,
    rank_ic_deterioration_labels,
)

__all__ = [
    "CalibrationBin",
    "ClassificationMetrics",
    "DecayLabels",
    "ExperimentManifest",
    "Fold",
    "PurgedWalkForwardSplit",
    "benjamini_hochberg",
    "calibration_bins",
    "circular_shift_placebo",
    "classification_metrics",
    "moving_block_bootstrap_ci",
    "paired_moving_block_difference_ci",
    "rank_ic_deterioration_labels",
    "write_experiment_manifest",
]
