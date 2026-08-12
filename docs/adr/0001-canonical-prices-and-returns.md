# ADR 0001: Canonical prices and returns

- Status: accepted
- Date: 2026-08-13
- Owners: data/factor workstream

## Context

AlphaWatch needs one auditable return series for signals, portfolios, costs, and diagnostics.
Public providers vary in whether `close` is raw, whether `adjusted_close` includes dividends,
and whether delisting proceeds exist. Combining adjusted prices with dividends can double-count
income; ignoring delistings can bias results; forward-filling a missing trading day creates a
fictitious zero return.

CRSP models delisting return explicitly and documents cases where it cannot establish a value.
Nasdaq's Daily List contains listings, delistings, dividends, and splits but is a subscription
product. Alpha Vantage documents raw OHLCV, adjusted close, dividends, and split coefficients,
but its daily adjusted endpoint is premium. Yahoo access is intended for personal use and is not
an appropriate production dependency. NYSE defines normal and early-close sessions in Eastern
Time, so calendar dates alone are insufficient availability timestamps.

## Decision

1. Retain raw OHLCV, adjusted close, dividend, split coefficient, and delisting return separately.
2. `price_return = close[t]/close[t-1]-1` is an audit series, not the principal performance return.
3. `total_return_proxy = adjusted_close[t]/adjusted_close[t-1]-1` is used only when the provider
   declares adjusted close to include splits and cash distributions.
4. If a verified `delisting_return` exists, the terminal return is compounded once:
   `(1 + total_return_proxy) * (1 + delisting_return) - 1`.
5. Never add a dividend to an adjusted-close return.
6. First observations, gaps, unresolved corporate-action jumps, and missing delisting outcomes are
   represented explicitly; they are never silently imputed.
7. Signals are formed after the official close and become tradable on the next valid session.
8. Bronze bytes and provider metadata are immutable. Corrections create new dataset versions.
9. A public-data run remains `survivorship_safe=false` unless the input manifest certifies active
   and delisted coverage plus historical membership.

## Consequences

The platform produces useful public-data research without making institutional-grade claims.
Replacing the provider changes adapters and manifests, not factor definitions. Research requiring
certified delisting outcomes remains blocked until a source such as CRSP or Sharadar is connected.

## Primary references

- [CRSP US Stock data definitions](https://www.crsp.org/crsp_pdf/crsp-us-stock-indexes-databases-data-descriptions-guide-crspaccess/)
- [Nasdaq Daily List](https://nasdaqtrader.com/Trader.aspx?id=DailyListPD)
- [NYSE hours and calendars](https://www.nyse.com/markets/hours-calendars)
- [Alpha Vantage API documentation](https://www.alphavantage.co/documentation/)
- [yfinance usage disclaimer](https://ranaroussi.github.io/yfinance/index.html)

