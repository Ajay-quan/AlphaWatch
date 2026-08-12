# Person 1 definition of done

- [x] Immutable Bronze bytes, run IDs, versions, timestamps and SHA-256 checksums
- [x] Versioned Silver and Gold Parquet with atomic writes and manifests
- [x] Permanent identity and effective-date ticker mapping
- [x] Strict UTC `available_at` invariant and leakage tests
- [x] Duplicate, range, null, missing-session and suspected-action reporting
- [x] Raw, adjusted, total and delisting-return semantics documented and tested
- [x] US session calendar with exceptional-closure extension points
- [x] Public SEC filing-vintage and current Nasdaq reference adapters
- [x] All twelve initial factor specifications and calculation layers
- [x] Missing-data preservation, winsorization, z-scores, ranks and neutralization
- [x] Equal/rank and positive-auxiliary value/volatility weighting primitives
- [x] Long-short weights, gross returns, turnover, versioned costs and net returns
- [x] Performance, tail, IC, rolling and exposure diagnostics
- [x] CLI workflows for ingestion, returns, fundamentals and factor backtests
- [x] Unit, golden, leakage, integration and regression-oriented tests in CI
- [x] PIT policy, ADR, data dictionary, methodology and public-data disclosures

## Certification boundary

The software assignment is complete with public adapters. Historical results remain
`survivorship_safe=false` until an input manifest certifies historical membership, delisted
securities and terminal outcomes. This is an external data property, not unfinished software.
CRSP/Compustat or Sharadar can be added behind the adapter contracts without changing factor APIs.
