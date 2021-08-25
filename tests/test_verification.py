import unittest
import pyrtl

import pyrtl_extras as pe

class TestVerification(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_equivalent_comb(self):
        # Very simple test of De Morgan's Law
        def f1(x, y):
            return ~x | ~y
        
        def f2(x, y):
            return ~(x & y)
        
        pe.equivalent_comb(f1, f2, [4, 4])

if __name__ == "__main__":
    unittest.main()
