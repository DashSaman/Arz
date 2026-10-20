import unittest

from research.xmoon.model import (
    Pivot,
    allocation_weights,
    basket_break_even,
    bounded_allocations,
    detect_three_push_from_pivots,
    ma200_alignment,
    rsi_extreme_alignment,
    step_levels,
    wilder_rsi,
)


class XmoonResearchTests(unittest.TestCase):
    def test_rsi_monotonic_rise_reaches_100(self):
        closes = [float(i) for i in range(1, 40)]
        values = wilder_rsi(closes, 14)
        self.assertEqual(values[14], 100.0)
        self.assertEqual(values[-1], 100.0)

    def test_three_push_long_reversal_uses_third_pivot_confirmation(self):
        pivots = [
            Pivot(10, 12, "low", 100.0, 25.0, "MINOR"),
            Pivot(20, 22, "low", 95.0, 30.0, "MINOR"),
            Pivot(30, 32, "low", 90.0, 36.0, "MID_MAJOR"),
        ]
        signals = detect_three_push_from_pivots(pivots)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].direction, "LONG_REVERSAL")
        self.assertEqual(signals[0].confirmed_at, 32)
        self.assertGreater(signals[0].confirmed_at, pivots[-1].index)

    def test_three_push_short_reversal(self):
        pivots = [
            Pivot(10, 12, "high", 100.0, 78.0, "MINOR"),
            Pivot(20, 22, "high", 105.0, 72.0, "MINOR"),
            Pivot(30, 32, "high", 110.0, 65.0, "MID_MAJOR"),
        ]
        signal = detect_three_push_from_pivots(pivots)[0]
        self.assertEqual(signal.direction, "SHORT_REVERSAL")

    def test_linear_dca_is_bounded_not_unlimited_recovery(self):
        weights = allocation_weights(4, "linear")
        self.assertEqual(
            [round(x, 2) for x in weights],
            [0.10, 0.20, 0.30, 0.40],
        )
        allocations = bounded_allocations(
            20.0,
            weights,
            max_basket_capital=20.0,
        )
        self.assertAlmostEqual(sum(allocations), 20.0)
        with self.assertRaises(ValueError):
            bounded_allocations(
                20.01,
                weights,
                max_basket_capital=20.0,
            )

    def test_break_even_rises_when_costs_are_added(self):
        entries = [100.0, 90.0]
        notionals = [10.0, 20.0]
        zero = basket_break_even(entries, notionals)
        costed = basket_break_even(
            entries,
            notionals,
            entry_pct_cost=0.002,
            exit_pct_cost=0.002,
            fixed_entry_cost_each=0.05,
            fixed_exit_cost=0.05,
        )
        self.assertGreater(costed.exit_price, zero.exit_price)

    def test_step_levels_move_only_against_the_hypothesis(self):
        long_levels = step_levels(
            100.0,
            4,
            direction="LONG_REVERSAL",
            mode="percent",
            spacing=0.02,
        )
        short_levels = step_levels(
            100.0,
            4,
            direction="SHORT_REVERSAL",
            mode="percent",
            spacing=0.02,
        )
        self.assertEqual(long_levels, [100.0, 98.0, 96.0, 94.0])
        self.assertEqual(short_levels, [100.0, 102.0, 104.0, 106.0])

    def test_public_confirmation_filters_are_minimal_and_directional(self):
        self.assertTrue(
            ma200_alignment(
                110.0,
                100.0,
                direction="LONG_REVERSAL",
            )
        )
        self.assertFalse(
            ma200_alignment(
                90.0,
                100.0,
                direction="LONG_REVERSAL",
            )
        )
        self.assertTrue(
            rsi_extreme_alignment(
                28.0,
                direction="LONG_REVERSAL",
            )
        )
        self.assertTrue(
            rsi_extreme_alignment(
                72.0,
                direction="SHORT_REVERSAL",
            )
        )


if __name__ == "__main__":
    unittest.main()
