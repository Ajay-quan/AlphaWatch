# Person 1 roadmap

## Milestone 1 — implemented foundation

- Canonical UTC-aware contracts and fail-closed PIT guard
- Temporal security master with overlap detection
- Immutable-ingestion manifest and SHA-256 utility
- Shared factor interface
- 12–1 momentum, short-term reversal, and low-volatility calculations
- Dollar-neutral rank portfolio and versioned transaction-cost model
- Golden and leakage tests

## Milestone 2 — provider-neutral data lake

- Provider adapter protocol, raw-response writer, atomic sidecar manifests
- Polars schema validation and DuckDB inspection utilities
- Idempotent Bronze-to-Silver normalization
- Adjustments, delistings, exchange calendar, duplicate/missingness policy
- Dataset-level quality reports and version manifests

## Milestone 3 — complete initial factor library

- Size, liquidity, turnover
- Value, profitability, investment, quality and accrual quality using filing timestamps
- Winsorization, standardization, sector/size neutralization
- Equal/value/volatility/rank weighting and holding-period overlap
- Gross/net returns and exposure diagnostics

## Data acquisition decision

Do not silently use free current-constituent lists for historical work. Choose a vendor
that supplies delisted securities, identifier history, corporate actions, filing/public
timestamps, and redistribution terms. Keep provider-specific fields behind adapters.

