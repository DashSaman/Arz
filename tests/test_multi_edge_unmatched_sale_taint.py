import unittest

from arz.multi_edge.accounting import FIFOBook, AverageCostBook
from tests.test_multi_edge_accounting import ev


class UnmatchedSaleQuarantineTests(unittest.TestCase):
    def sample(self):
        return [
            ev('01','buy',1,10,ts=100,block=1),
            ev('02','sell',2,40,ts=200,block=2),
            ev('03','sell',1,100,ts=300,block=3),
        ]

    def test_unmatched_sale_cannot_be_reused_for_later_fake_profit_fifo(self):
        result=FIFOBook().process(self.sample(),cutoff=400)
        self.assertEqual(result["cycles"],[])
        self.assertEqual([u["reason"] for u in result["unresolved_events"]],
                         ["INSUFFICIENT_COST_BASIS","PRIOR_UNMATCHED_SALE_TAINT"])
        self.assertEqual(result["cost_basis_coverage"],0)
        self.assertEqual(len(result["tainted_positions"]),1)

    def test_unmatched_sale_cannot_be_reused_for_later_fake_profit_average(self):
        result=AverageCostBook().process(self.sample(),cutoff=400)
        self.assertEqual(len(result["cycles"]),0)
        self.assertEqual(result["unresolved_events"][1]["reason"],"PRIOR_UNMATCHED_SALE_TAINT")

    def test_new_purchase_after_unknown_sale_does_not_clear_taint(self):
        events=[
            ev('01','sell',3,100,ts=100,block=1),
            ev('02','buy',10,200,ts=200,block=2),
            ev('03','sell',2,1000,ts=300,block=3),
        ]
        for book in (FIFOBook(),AverageCostBook()):
            with self.subTest(book=book.method):
                result=book.process(events,cutoff=400)
                self.assertEqual(result["cycles"],[])
                self.assertEqual(result["unresolved_events"][1]["reason"],"PRIOR_UNMATCHED_SALE_TAINT")

    def test_one_wallet_taint_does_not_poison_other_wallet(self):
        events=[
            ev('01','buy',1,10,ts=100,block=1,wallet="0xa"),
            ev('02','sell',2,20,ts=200,block=2,wallet="0xa"),
            ev('03','buy',1,10,ts=210,block=3,wallet="0xb"),
            ev('04','sell',1,15,ts=300,block=4,wallet="0xb"),
        ]
        result=FIFOBook().process(events,cutoff=400)
        self.assertEqual(len(result["cycles"]),1)
        self.assertEqual(result["cycles"][0]["wallet"],"0xb")
        self.assertAlmostEqual(result["cycles"][0]["net_pnl"],5)
        self.assertEqual(result["tainted_positions"][0]["wallet"],"0xa")

    def test_honest_partial_sale_remains_valid_before_unmatched_gap(self):
        events=[
            ev('01','buy',2,20,ts=100,block=1),
            ev('02','sell',1,15,ts=200,block=2),
            ev('03','sell',2,30,ts=300,block=3),
            ev('04','sell',.5,50,ts=400,block=4),
        ]
        res=FIFOBook().process(events,cutoff=500)
        self.assertEqual(len(res["cycles"]),1)
        self.assertAlmostEqual(res["cycles"][0]["net_pnl"],5)
        self.assertEqual(res["unresolved_events"][-1]["reason"],"PRIOR_UNMATCHED_SALE_TAINT")
        self.assertAlmostEqual(res["cost_basis_coverage"],1/3.5)

    def test_preexisting_complete_trades_unchanged(self):
        events=[ev('01','buy',2,20,ts=100,block=1),
                ev('02','sell',2,30,ts=200,block=2)]
        for book in (FIFOBook(),AverageCostBook()):
            out=book.process(events,cutoff=300)
            self.assertEqual(out["tainted_positions"],[])
            self.assertEqual(out["cost_basis_coverage"],1)
            self.assertAlmostEqual(out["cycles"][0]["net_pnl"],10)


if __name__=="__main__":
    unittest.main()
