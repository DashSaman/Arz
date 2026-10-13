import unittest
import arz_phase4_scope as m

class ScopeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(m,'same_tick_spacing_cell'), 'Independent scope proof missing')

    def test_positive_gas_counter_does_not_alone_imply_crossing(self):
        p=3830260098844831746376465;after=3830260757477967344255240
        proof=m.same_tick_spacing_cell(p,after,10)
        self.assertTrue(proof['certified']);self.assertEqual(proof['lower_tick'],-198760)
        r=m.compare_quote_with_scope(p,1202316496893574204,10000000,500,False,[4276469299898715,after,1,86255],10)
        self.assertTrue(r['passed']);self.assertEqual(r['reported_gas_tick_counter'],1)

    def test_exact_boundary_is_not_inside_cell(self):
        self.assertFalse(m.same_tick_spacing_cell(m.Q96,m.Q96+100,10)['certified'])

    def test_crossing_a_spacing_boundary_is_not_certified(self):
        boundary=m.Q96*10001//10000
        self.assertFalse(m.same_tick_spacing_cell(boundary-1000,boundary+1000,2)['certified'])

    def test_correct_scope_does_not_hide_output_error(self):
        p=3830260098844831746376465;after=3830260757477967344255240
        r=m.compare_quote_with_scope(p,1202316496893574204,10000000,500,False,[4276469299898715+2,after,1,86255],10)
        self.assertFalse(r['passed'])

    def test_invalid_spacing_is_not_accepted(self):
        for x in (True,0,-1,1.5):
            with self.assertRaises(ValueError):m.same_tick_spacing_cell(m.Q96+100,m.Q96+1000,x)
