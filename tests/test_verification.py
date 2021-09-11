import unittest
import pyrtl

import pyrtl_extras as pe

class TestVerificationViaSimulation(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_equivalent_comb(self):
        # Very simple test of De Morgan's Law
        def f1(x, y):
            return ~x | ~y
        
        def f2(x, y):
            return ~(x & y)
        
        pe.equivalent_comb_via_sim(f1, f2, [4, 4])

class TestVerificationViaModelChecking(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_equivalent_seq1(self):
        def f1(x, y):
            r1 = pyrtl.Register(len(x))
            r2 = pyrtl.Register(len(y))
            r1.next <<= x
            r2.next <<= y
            return r1 + r2

        def f2(x, y):
            w = x + y
            r = pyrtl.Register(len(w))
            r.next <<= w
            return r

        pe.equivalent_seq_via_cosa(f1, f2, [4, 4])

if __name__ == "__main__":
    unittest.main()
