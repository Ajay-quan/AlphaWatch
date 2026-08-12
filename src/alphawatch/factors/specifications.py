from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FactorSpecification:
    name: str
    version: str
    direction: int
    formula: str
    required_fields: tuple[str, ...]
    availability_rule: str


FACTOR_SPECIFICATIONS = {
    spec.name: spec
    for spec in (
        FactorSpecification(
            "momentum_12_minus_1",
            "1.0.0",
            1,
            "P[t-21]/P[t-252]-1",
            ("adjusted_close",),
            "close_known",
        ),
        FactorSpecification(
            "short_term_reversal",
            "1.0.0",
            -1,
            "-(P[t]/P[t-21]-1)",
            ("adjusted_close",),
            "close_known",
        ),
        FactorSpecification(
            "value",
            "1.0.0",
            1,
            "book_equity/market_cap",
            ("book_equity", "market_cap"),
            "filing_and_price_known",
        ),
        FactorSpecification(
            "size", "1.0.0", 1, "-log(market_cap)", ("market_cap",), "price_and_shares_known"
        ),
        FactorSpecification(
            "profitability",
            "1.0.0",
            1,
            "operating_profit/book_equity",
            ("operating_profit", "book_equity"),
            "filing_known",
        ),
        FactorSpecification(
            "investment",
            "1.0.0",
            1,
            "-(assets/assets_lag-1)",
            ("total_assets", "total_assets_lag"),
            "both_filings_known",
        ),
        FactorSpecification(
            "quality",
            "1.0.0",
            1,
            "CFO/assets-|accruals|/assets",
            ("cash_flow_operations", "accruals", "total_assets"),
            "filing_known",
        ),
        FactorSpecification(
            "low_volatility",
            "1.0.0",
            1,
            "-annualized_std(log_returns)",
            ("adjusted_close",),
            "close_known",
        ),
        FactorSpecification(
            "beta", "1.0.0", -1, "cov(r_i,r_m)/var(r_m)", ("return", "market_return"), "close_known"
        ),
        FactorSpecification(
            "liquidity", "1.0.0", 1, "mean(log(dollar_volume))", ("dollar_volume",), "close_known"
        ),
        FactorSpecification(
            "turnover", "1.0.0", -1, "mean(volume/shares_outstanding)", ("turnover",), "close_known"
        ),
        FactorSpecification(
            "accrual_quality",
            "1.0.0",
            1,
            "-accruals/assets",
            ("accruals", "total_assets"),
            "filing_known",
        ),
    )
}
