import unittest
import math
import pyrtl
import pyrtl_extras as pe

class TestFloatingPoint(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_fp_add(self):
        a, b = pyrtl.input_list('a/16 b/16')
        res = pe.fp_add(a, b, precision='half')
        pyrtl.probe(res, 'res')
        sim = pyrtl.Simulation()
        sim.step({
            'a': 0b0011100000000000, # 0.5
            'b': 0b0100011100000000, # 3.75
        })
        # Should be 4.25
        # TODO
        #sim.tracer.render_trace(repr_func=pe.binf(16, 16), symbol_len=None)

    def test_fp_to_float_single_precision(self):
        self.assertEqual(
            pe.fp_to_float(0b01000011101001001011001000000000, precision='single'),
            329.390625
        )
        self.assertEqual(
            pe.fp_to_float(0b10111111010000000000000000000000, precision='single'),
            -0.75
        )
        self.assertEqual(
            pe.fp_to_float(0b11000000101000000000000000000000, precision='single'),
            -5.0
        )
        self.assertEqual(
            pe.fp_to_float(0b00111110001000000000000000000000, precision='single'),
            0.15625
        )

    def test_float_to_fp_single_precision_normal(self):
        self.assertEqual(
            pe.float_to_fp(329.390625, precision='single'),
            0b01000011101001001011001000000000
        )
        self.assertEqual(
            pe.float_to_fp(-0.75, precision='single'),
            0b10111111010000000000000000000000
        )
        self.assertEqual(
            pe.float_to_fp(-5.0, precision='single'),
            0b11000000101000000000000000000000
        )
        self.assertEqual(
            pe.float_to_fp(0.15625, precision='single'),
            0b00111110001000000000000000000000
        )

    def test_float_to_fp_single_precision_other(self):
        self.assertEqual(
            pe.float_to_fp(0.0, precision='single'),
            0
        )

    def test_fp_to_float_half_precision(self):
        self.assertEqual(
            pe.fp_to_float(0, precision='half'),
            0.0
        )
        self.assertEqual(
            pe.fp_to_float(-0, precision='half'),
            0.0
        )
        self.assertEqual(
            pe.fp_to_float(0b0111110000000000, precision='half'),
            math.inf
        )
        self.assertEqual(
            pe.fp_to_float(0b1111110000000000, precision='half'),
            -math.inf
        )
        self.assertTrue(
            math.isnan(pe.fp_to_float(0b0111110000000001, precision='half'))
        )
        self.assertTrue(
            math.isnan(pe.fp_to_float(0b1111110000000001, precision='half'))
        )

    def test_float_in_range_half_precision(self):
        # Min negative
        self.assertFalse(pe.float_in_range(-65505, precision='half'))
        self.assertTrue(pe.float_in_range(-65504, precision='half'))
        self.assertTrue(pe.float_in_range(-65503, precision='half'))
        # Max negative
        self.assertTrue(pe.float_in_range(-2 ** -14 - (2 ** -15), precision='half'))
        self.assertTrue(pe.float_in_range(-2 ** -14, precision='half'))
        self.assertFalse(pe.float_in_range(-2 ** -14 + (2 ** -15), precision='half'))
        # Min positive
        self.assertFalse(pe.float_in_range(2 ** -14 - (2 ** -15), precision='half'))
        self.assertTrue(pe.float_in_range(2 ** -14, precision='half'))
        self.assertTrue(pe.float_in_range(2 ** -14 + (2 ** -15), precision='half'))
        # Max positive
        self.assertTrue(pe.float_in_range(65503, precision='half'))
        self.assertTrue(pe.float_in_range(65504, precision='half'))
        self.assertFalse(pe.float_in_range(65505, precision='half'))

    # TODO check for other precision ranges
    # TODO check for zero/Nan/infinity

    # TODO for use with tests using actual wires
        # a = pyrtl.Input(32, 'a')
        # res = pe.fp_to_float(a, precision='single')
        # pyrtl.probe(res, 'res')
        # sim = pyrtl.Simulation()
        # sim.step_multiple({
        #     'a': [
        #         0b10111111010000000000000000000000,
        #         0b11000000101000000000000000000000,
        #         0b00111110001000000000000000000000,
        #     ]
        # })
        # self.assertEqual(
        #     sim.tracer.trace['a'],
        #     [-0.75, -5.0, 0.15625]
        # )


if __name__ == "__main__":
    unittest.main()