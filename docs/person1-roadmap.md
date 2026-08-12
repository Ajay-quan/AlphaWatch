# Person 1 roadmap

## Current audited status

Person 1's public-data engineering scope is release-ready. The remaining unchecked acceptance
items require a licensed or otherwise certified historical-security source, which the project has
explicitly declined to purchase. Public-data research therefore remains correctly labeled
`survivorship_safe=false`; this is an empirical-data limitation rather than unfinished factor code.

## Milestone 1 — implemented foundation

- Canonical UTC-aware contracts and fail-closed PIT guard
- Temporal security master with overlap detection
- Immutable-ingestion manifest and SHA-256 utility
- Shared factor interface
- 12–1 momentum, short-term reversal, and low-volatility calculations
- Dollar-neutral rank portfolio and versioned transaction-cost model
- Golden and leakage tests

## Milestone 2 — provider-neutral data lake (implemented foundation)

- Provider adapter protocol, raw-response writer, atomic sidecar manifests — complete
- SEC Company Facts and Nasdaq current-symbol adapters — complete
- Public daily-price CSV contract — complete
- Polars schema validation and Parquet version manifests — complete
- Duplicate, range, null, and PIT rejection — complete
- Adjustments, delistings, and exchange-calendar normalization — provider dependent

## Milestone 3 — initial factor library (calculation layer implemented)

- Price factors: momentum, reversal, low volatility — complete
- Market factors: beta, liquidity, turnover — complete
- Fundamental formulas: size, value, profitability, investment, quality, accruals — complete
- Winsorization, standardization, ranking, numeric neutralization — complete
- Equal and auxiliary weighting — complete
- Rolling portfolios, holding-period overlap, liquidity caps, and diagnostics — complete

## Data acquisition decision

Do not silently use free current-constituent lists for historical work. Choose a vendor
that supplies delisted securities, identifier history, corporate actions, filing/public
timestamps, and redistribution terms. Keep provider-specific fields behind adapters.

For the public-data build, current snapshots are archived prospectively and research
outputs are explicitly marked non-survivorship-safe. This is a methodological disclosure,
not a software defect that can be repaired by guessing historical constituents.
