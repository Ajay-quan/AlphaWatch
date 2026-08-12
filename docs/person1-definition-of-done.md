# Person 1 definition of done

This is an acceptance checklist, not a declaration of current completion. A checkbox may be marked
only when the capability works through the public CLI from a fresh installation and has appropriate
tests. Current progress is tracked in `person1-roadmap.md`.

## Data platform

- [x] Bronze payloads retain source, period, versions, timestamp, run ID and SHA-256
- [x] Bronze writes are transactionally complete and recoverable after interruption
- [x] Silver/Gold local Parquet artifacts and manifests exist
- [x] Dataset versions are immutable (local reference implementation writes versioned Parquet)
- [x] A real public price adapter connects directly to canonical Silver returns
- [ ] Corporate actions, delistings and missing outcomes are normalized from source data
- [ ] A historical, survivorship-aware universe is available or externally certified

## Identity and point-in-time correctness

- [x] Permanent security IDs and temporal ticker lookup primitive
- [x] Persistent identifier crosswalk including CIK and provider identifiers
- [ ] Historical sector/industry and universe membership joins
- [x] UTC availability rejection for prices and fundamentals
- [x] End-to-end PIT/leakage tests for source availability and rolling features

## Factor system

- [x] Price factor classes for momentum, reversal and low volatility
- [x] Raw formula prototypes for the other nine initial factors
- [x] All twelve factors implement one shared, versioned, configuration-driven interface
- [x] SEC facts normalize into canonical PIT fundamental inputs automatically
- [x] Every factor supports missingness, winsorization, ranking and sector/size neutralization

## Portfolios, costs and diagnostics

- [x] Basic equal-weight long-short tail backtest
- [x] Equal, value, volatility and rank weighting in the production backtest
- [x] Rebalance schedules, holding periods, overlapping cohorts and liquidity constraints
- [x] Exit-aware turnover, AUM-scaled impact and liquidity-sensitive transaction costs
- [x] Core performance, IC, tail and exposure metric primitives
- [x] Persisted dated diagnostics and aggregate factor summaries
- [x] Quantile monotonicity and IC information-ratio reports

## Verification and release

- [x] Unit tests, linting, typing and coverage threshold
- [ ] Authoritative golden datasets and regression snapshots
- [x] Property-based tests for mathematical invariants
- [x] Provider-parser integration tests and full CLI end-to-end test
- [x] Fresh-install wheel and console-script certification (Python 3.14)
- [ ] Clean repository release with no contradictory completion claims

## Certification boundary

Even after software completion, public historical results remain `survivorship_safe=false` unless
the input source certifies historical membership, delisted securities and terminal outcomes. This
does not excuse incomplete engineering; it limits the empirical claims allowed from public inputs.
