# Public-data methodology and limitations

## Chosen prototype sources

- SEC EDGAR Company Facts for standardized public financial facts and filing vintages.
- Nasdaq Trader symbol-directory snapshots for current reference metadata.
- Strict provider-neutral OHLCV CSV ingestion for public daily prices.

SEC Company Facts is updated as submissions are disseminated and includes accession and
filing metadata. Because its observations expose a filing date rather than a guaranteed
first-public byte timestamp, AlphaWatch conservatively assigns availability to the next
UTC day plus five minutes. This sacrifices some timeliness to reduce leakage risk.

Nasdaq describes the downloadable directory as current-day information. AlphaWatch archives
each acquisition but never backfills the current list across history. Therefore a study that
starts today can become prospectively survivorship-aware, while a historical public-data
prototype remains explicitly marked `survivorship_safe: false`.

## Default portfolio convention

- Reference capital: USD 10 million
- Gross long exposure: 50%
- Gross short exposure: 50%
- Signal timestamp: market close
- Assumed execution: next session close
- Maximum participation: 1% of average daily dollar volume
- Rebalance frequency: monthly
- Tail selection: top and bottom 20%

The public prototype cost model uses 0.5 bps commission, 5 bps half-spread, 2.5 bps
slippage, and a 10 bps quadratic coefficient. Every result must retain the cost-model
version. These are conservative teaching/research defaults; they require calibration before
any live capital decision.

## Claims that are prohibited

- Calling a current-symbol backtest survivorship-safe
- Calling provider-adjusted prices independently verified corporate-action returns
- Treating SEC filing date as exact intraday public availability
- Presenting the default cost model as broker- or portfolio-calibrated
- Describing public-data results as investable performance
