from __future__ import annotations

import math
import unittest
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from alphawatch.data.contracts import PriceBar
from alphawatch.data.pit import assert_point_in_time
from alphawatch.exceptions import DataContractError, IdentityResolutionError, LookAheadError
from alphawatch.factors.base import FactorContext
from alphawatch.factors.price import LowVolatility, Momentum12Minus1, ShortTermReversal
from alphawatch.portfolio.construction import rank_long_short, turnover
from alphawatch.portfolio.costs import LinearQuadraticCostModel
from alphawatch.security_master.master import SecurityMaster, SymbolMapping

UTC = UTC


def bars(count: int, growth: float = 1.01, security_id: str = "sec-1") -> list[PriceBar]:
    start = date(2020, 1, 1)
    return [
        PriceBar(
            security_id=security_id,
            session=start + timedelta(days=i),
            available_at=datetime(2020, 1, 1, tzinfo=UTC) + timedelta(days=i, hours=23),
            adjusted_close=Decimal(str(100 * growth**i)),
            dollar_volume=Decimal("1000000"),
        )
        for i in range(count)
    ]


class PointInTimeTests(unittest.TestCase):
    def test_future_record_fails_closed(self) -> None:
        rows = bars(2)
        with self.assertRaises(LookAheadError):
            assert_point_in_time(rows, rows[0].available_at)

    def test_naive_timestamp_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            PriceBar("x", date.today(), datetime.now(), Decimal("1"))


class SecurityMasterTests(unittest.TestCase):
    def test_temporal_ticker_reuse(self) -> None:
        master = SecurityMaster(
            [
                SymbolMapping("old", "ABC", date(2000, 1, 1), date(2010, 12, 31), "XNYS"),
                SymbolMapping("new", "ABC", date(2011, 1, 1), None, "XNYS"),
            ]
        )
        self.assertEqual(master.resolve("ABC", "XNYS", date(2005, 1, 1)), "old")
        self.assertEqual(master.resolve("ABC", "XNYS", date(2020, 1, 1)), "new")
        with self.assertRaises(IdentityResolutionError):
            master.resolve("ABC", "XNAS", date(2020, 1, 1))

    def test_overlap_is_rejected(self) -> None:
        with self.assertRaises(DataContractError):
            SecurityMaster(
                [
                    SymbolMapping("a", "ABC", date(2000, 1, 1), date(2010, 1, 1), "XNYS"),
                    SymbolMapping("b", "ABC", date(2010, 1, 1), None, "XNYS"),
                ]
            )


class FactorTests(unittest.TestCase):
    def test_momentum_skips_latest_period(self) -> None:
        rows = bars(6, growth=1.1)
        context = FactorContext(rows[-1].available_at, minimum_observations=1)
        result = Momentum12Minus1(lookback=5, skip=2).compute(rows, context)[0]
        self.assertAlmostEqual(result.raw_value or 0, 1.1**3 - 1)

    def test_reversal_has_opposite_return_sign(self) -> None:
        rows = bars(3, growth=1.1)
        context = FactorContext(rows[-1].available_at, minimum_observations=1)
        value = ShortTermReversal(lookback=2).compute(rows, context)[0].raw_value
        self.assertAlmostEqual(value or 0, -(1.1**2 - 1))

    def test_constant_growth_has_zero_log_return_volatility(self) -> None:
        rows = bars(5, growth=1.01)
        context = FactorContext(rows[-1].available_at, minimum_observations=1)
        value = LowVolatility(lookback=4).compute(rows, context)[0].raw_value
        self.assertTrue(math.isclose(value or 0, 0.0, abs_tol=1e-12))


class PortfolioTests(unittest.TestCase):
    def test_weights_are_dollar_neutral_and_unit_gross(self) -> None:
        rows = bars(2)
        context = FactorContext(rows[-1].available_at, minimum_observations=1)
        template = ShortTermReversal(1).compute(rows, context)[0]
        signals = [
            type(template)(str(i), template.as_of, template.available_at, "x", "1", float(i))
            for i in range(10)
        ]
        weights = rank_long_short(signals, 0.2)
        self.assertAlmostEqual(sum(w.weight for w in weights), 0.0)
        self.assertAlmostEqual(sum(abs(w.weight) for w in weights), 1.0)

    def test_turnover_and_cost(self) -> None:
        value = turnover({"a": 0.5, "b": -0.5}, {"a": 0.25, "b": -0.25})
        self.assertAlmostEqual(value, 0.25)
        model = LinearQuadraticCostModel("1", 1, 2, 3, 4)
        self.assertAlmostEqual(model.estimate(0.5), (6 * 0.5 + 4 * 0.25) / 10_000)


if __name__ == "__main__":
    unittest.main()
