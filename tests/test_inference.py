import numpy as np

from alphawatch.research.inference import benjamini_hochberg, moving_block_bootstrap_mean_ci


def test_block_bootstrap_is_reproducible_and_contains_constant_mean() -> None:
    ci = moving_block_bootstrap_mean_ci([0.02] * 20, block_size=4, n_resamples=200, seed=17)
    assert np.isclose(ci.estimate, 0.02)
    assert np.isclose(ci.lower, 0.02)
    assert np.isclose(ci.upper, 0.02)


def test_benjamini_hochberg_returns_monotone_adjusted_values() -> None:
    results = benjamini_hochberg({"H1": 0.01, "H2": 0.03, "H3": 0.20}, 0.05)
    assert [item.hypothesis_id for item in results] == ["H1", "H2", "H3"]
    assert [item.rejected for item in results] == [True, True, False]
    assert [item.adjusted_p_value for item in results] == sorted(item.adjusted_p_value for item in results)
