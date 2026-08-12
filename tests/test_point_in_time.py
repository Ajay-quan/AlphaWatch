from datetime import datetime, timedelta

import pytest

from alphawatch.research.contracts import (
    AvailabilityViolation,
    TimedLabel,
    TimedObservation,
    assert_available_as_of,
    assert_labels_resolved_as_of,
)


def test_known_observation_is_allowed() -> None:
    now = datetime(2020, 1, 10)
    assert_available_as_of(
        [TimedObservation("A", now - timedelta(days=2), now - timedelta(days=1), 1.0)], now
    )


def test_future_fundamental_is_a_production_failure() -> None:
    now = datetime(2020, 1, 10)
    future_filing = TimedObservation("A", now - timedelta(days=90), now + timedelta(days=1), 1.0)
    with pytest.raises(AvailabilityViolation, match="available_at"):
        assert_available_as_of([future_filing], now)


@pytest.mark.parametrize(
    "data_class",
    [
        "macro revision",
        "institutional filing",
        "corporate action",
        "universe membership",
        "rolling statistic",
    ],
)
def test_all_point_in_time_data_classes_fail_closed_when_future(data_class: str) -> None:
    now = datetime(2020, 1, 10)
    future_observation = TimedObservation(
        data_class, now - timedelta(days=30), now + timedelta(days=1), 1.0
    )
    with pytest.raises(AvailabilityViolation, match="available_at"):
        assert_available_as_of([future_observation], now)


def test_unresolved_forward_label_is_a_production_failure() -> None:
    now = datetime(2020, 1, 10)
    label = TimedLabel(now - timedelta(days=5), now + timedelta(days=1), 1.0)
    with pytest.raises(AvailabilityViolation, match="unresolved"):
        assert_labels_resolved_as_of([label], now)


def test_invalid_timestamp_order_and_non_finite_observation_are_rejected() -> None:
    now = datetime(2020, 1, 10)
    with pytest.raises(ValueError, match="availability"):
        TimedObservation("A", now, now - timedelta(days=1), 1.0)
    with pytest.raises(ValueError, match="finite"):
        TimedObservation("A", now, now, float("nan"))
