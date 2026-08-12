"""Guardrails that prevent claims from exceeding the experiment evidence."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .contracts import ResearchIntegrityError
from .hypotheses import ResearchPhase
from .inference import ConfidenceInterval


class ConclusionStrength(str, Enum):
    INCONCLUSIVE = "inconclusive"
    ASSOCIATION = "out_of_sample_association"
    ROBUST_ASSOCIATION = "robust_out_of_sample_association"


@dataclass(frozen=True)
class EvidenceBundle:
    phase: ResearchPhase
    final_test_untouched: bool
    point_in_time_passed: bool
    multiplicity_controlled: bool
    baseline_beaten: bool
    confidence_interval: ConfidenceInterval
    robustness_checks_passed: int
    robustness_checks_total: int


def assess_conclusion(evidence: EvidenceBundle) -> ConclusionStrength:
    """Return only a conservative associative conclusion; never claims causality."""
    if evidence.robustness_checks_passed > evidence.robustness_checks_total:
        raise ResearchIntegrityError("robustness-check count is invalid")
    if not evidence.point_in_time_passed or not evidence.final_test_untouched:
        return ConclusionStrength.INCONCLUSIVE
    ci_positive = evidence.confidence_interval.lower > 0
    if not (evidence.baseline_beaten and evidence.multiplicity_controlled and ci_positive):
        return ConclusionStrength.INCONCLUSIVE
    if (
        evidence.phase is ResearchPhase.CONFIRMATORY
        and evidence.robustness_checks_total > 0
        and evidence.robustness_checks_passed == evidence.robustness_checks_total
    ):
        return ConclusionStrength.ROBUST_ASSOCIATION
    return ConclusionStrength.ASSOCIATION
