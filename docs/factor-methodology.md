# Initial factor methodology

The executable registry is `alphawatch.factors.specifications.FACTOR_SPECIFICATIONS`.
All signals are oriented so a larger value is the preferred long direction.

- Momentum: adjusted price from approximately 12 months ago through one month ago.
- Reversal: negative recent one-month return.
- Value: book equity divided by market capitalization.
- Size: negative log market capitalization.
- Profitability: operating profit divided by book equity.
- Investment: negative year-over-year asset growth.
- Quality: operating cash flow intensity less absolute accrual intensity.
- Low volatility: negative annualized standard deviation of daily log returns.
- Beta: rolling covariance with the market divided by rolling market variance; low beta preferred.
- Liquidity: rolling mean log dollar volume.
- Turnover: rolling mean share turnover; lower turnover is preferred in the canonical orientation.
- Accrual quality: negative accruals divided by assets.

Fundamental inputs use filing vintages selected solely by `available_at`. Cross-sectional processing
winsorizes tails, removes sector means when configured, standardizes, and ranks. Missing values remain
missing. Each experiment records factor and configuration versions.

