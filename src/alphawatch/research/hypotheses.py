"""Preregistered hypothesis contracts; exploratory findings cannot overwrite these."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum

from .contracts import ResearchIntegrityError


class ResearchPhase(str, Enum):
    EXPLORATORY = "exploratory"
    CONFIRMATORY = "confirmatory"


@dataclass(frozen=True)
class HypothesisSpec:
    hypothesis_id: str
    statement: str
    dependent_variable: str
    independent_variables: tuple[str, ...]
    null_hypothesis: str
    test: str
    economic_interpretation: str
    robustness_checks: tuple[str, ...]
    start_date: date
    end_date: date
    alpha: float = 0.05

    def validate(self) -> None:
        required = (
            self.hypothesis_id,
            self.statement,
            self.dependent_variable,
            self.null_hypothesis,
            self.test,
            self.economic_interpretation,
        )
        if not all(required) or not self.independent_variables or not self.robustness_checks:
            raise ResearchIntegrityError("hypothesis specification is incomplete")
        if self.start_date >= self.end_date or not 0 < self.alpha < 1:
            raise ResearchIntegrityError("hypothesis period or alpha is invalid")


def default_hypotheses(start_date: date, end_date: date) -> tuple[HypothesisSpec, ...]:
    """The five required hypotheses, fixed before confirmatory testing."""
    shared_checks = ("alternative horizons", "factor-family stratification", "block bootstrap CI")
    return (
        HypothesisSpec("H1", "Higher crowding predicts future Rank IC deterioration.", "future Rank IC deterioration", ("lagged crowding proxies",), "Crowding coefficients are zero.", "purged walk-forward logistic regression with block-bootstrap CI", "Tests whether crowding precedes predictive weakening, not whether it causes it.", shared_checks, start_date, end_date),
        HypothesisSpec("H2", "Crowding predicts drawdown and tail risk more strongly than mean return deterioration.", "future drawdown, CVaR, and mean return deterioration", ("lagged crowding proxies",), "Predictive performance is equal across targets.", "paired walk-forward score comparison with bootstrap CI", "Separates fragile implementation risk from average-return effects.", shared_checks, start_date, end_date),
        HypothesisSpec("H3", "Structural indicators provide earlier warning than trailing-performance indicators.", "time to confirmed deterioration", ("structural-break statistics", "trailing Sharpe", "trailing return"), "Detection delay is equal or longer for structural indicators.", "paired event-level detection-delay test", "Earlier detection is useful only if false-alarm rates remain controlled.", ("synthetic breaks", "matched false-alarm rate", "alternative confirmation rules"), start_date, end_date),
        HypothesisSpec("H4", "Crowding and decay dynamics differ across factor families.", "future deterioration", ("crowding proxies", "factor family interactions"), "Interaction coefficients are zero.", "hierarchical/interaction regression with multiplicity control", "Heterogeneity does not establish a common mechanism.", shared_checks, start_date, end_date),
        HypothesisSpec("H5", "A combined health model improves on performance-only baselines out of sample.", "future deterioration", ("health", "crowding", "regime", "liquidity", "structural instability"), "Out-of-sample score improvement is zero.", "nested purged walk-forward model comparison", "Any predictive uplift must survive costs, calibration, and uncertainty checks.", ("performance-only baseline", "calibration", "economic policy simulation", "final untouched test"), start_date, end_date),
    )
