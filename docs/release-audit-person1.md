# Person 1 release audit

Status: **public-data engineering scope certified on 2026-08-13**.

The audit requires a clean fresh installation, a real input dataset flowing through Bronze, Silver
and Gold, all twelve factors, costed portfolio returns, diagnostics, immutable lineage, and the full
test matrix. Passing unit tests alone is insufficient.

Verified release evidence:

- 85 tests pass with 86.73% statement coverage
- Ruff and strict mypy pass across the package
- A clean isolated Python 3.14 wheel installation and `alphawatch --help` pass
- Bronze payload and manifest finalization is atomic; analytical versions reject overwrites
- Alpha Vantage prices flow to canonical returns and a rolling public universe
- SEC facts normalize point-in-time into canonical fundamental inputs
- All twelve configured factors use the shared lifecycle
- Four weighting modes, rebalance intervals, overlapping holdings, position/ADV caps, exit-aware
  turnover, and liquidity-sensitive costs run through the CLI
- Dated IC and quantile diagnostics plus aggregate IC-IR/monotonicity summaries persist to Gold
- Property, regression, leakage, provider-parser, and CLI end-to-end tests pass

Certification does not claim survivorship-safe historical research. Free public inputs do not
certify historical membership, delisted securities, or every terminal outcome. Such runs must keep
`survivorship_safe=false`; resolving that empirical limitation requires an independently certified
dataset and is outside the explicitly selected free-data boundary.
