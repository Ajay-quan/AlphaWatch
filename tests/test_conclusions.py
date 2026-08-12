from alphawatch.research.conclusions import ConclusionStrength, EvidenceBundle, assess_conclusion
from alphawatch.research.hypotheses import ResearchPhase
from alphawatch.research.inference import ConfidenceInterval


def test_missing_point_in_time_validation_forces_inconclusive() -> None:
    evidence = EvidenceBundle(
        phase=ResearchPhase.CONFIRMATORY,
        final_test_untouched=True,
        point_in_time_passed=False,
        multiplicity_controlled=True,
        baseline_beaten=True,
        confidence_interval=ConfidenceInterval(0.2, 0.01, 0.4, 0.95),
        robustness_checks_passed=3,
        robustness_checks_total=3,
    )
    assert assess_conclusion(evidence) is ConclusionStrength.INCONCLUSIVE


def test_complete_confirmatory_evidence_is_associative_not_causal() -> None:
    evidence = EvidenceBundle(
        phase=ResearchPhase.CONFIRMATORY,
        final_test_untouched=True,
        point_in_time_passed=True,
        multiplicity_controlled=True,
        baseline_beaten=True,
        confidence_interval=ConfidenceInterval(0.2, 0.01, 0.4, 0.95),
        robustness_checks_passed=3,
        robustness_checks_total=3,
    )
    assert assess_conclusion(evidence) is ConclusionStrength.ROBUST_ASSOCIATION


def test_confirmatory_result_without_preregistered_robustness_checks_is_not_robust() -> None:
    evidence = EvidenceBundle(
        phase=ResearchPhase.CONFIRMATORY,
        final_test_untouched=True,
        point_in_time_passed=True,
        multiplicity_controlled=True,
        baseline_beaten=True,
        confidence_interval=ConfidenceInterval(0.2, 0.01, 0.4, 0.95),
        robustness_checks_passed=0,
        robustness_checks_total=0,
    )
    assert assess_conclusion(evidence) is ConclusionStrength.ASSOCIATION
