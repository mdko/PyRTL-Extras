import pyrtl
import unittest

import pyrtl_extras as pe


class TestShifters(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_lfsr(self):
        out1 = pe.lfsr(0xace1, 16, [10, 12, 13, 15])  # using list of bits
        out2 = pe.lfsr(0xace1, 16, 0xb400)  # use bitmask
        pyrtl.probe(out1, 'out1')
        pyrtl.probe(out2, 'out2')
        sim = pyrtl.Simulation()
        sim.step_multiple(nsteps=100)
        self.assertEqual(sim.tracer.trace['out1'], sim.tracer.trace['out2'])

    def test_lsfr_2(self):
        # https://www.cs.princeton.edu/courses/archive/spring11/cos126/demos/00demo-lfsr.pptx
        out = pe.lfsr(0b01101000010, 11, [10, 8])
        pyrtl.probe(out, 'out')
        sim = pyrtl.Simulation()
        sim.step_multiple(nsteps=8)
        # sim.tracer.render_trace(symbol_len=15, repr_func=bin)
        self.assertEqual(sim.tracer.trace['out'], [
            0b01101000010,
            0b11010000101,
            0b10100001011,
            0b01000010110,
            0b10000101100,
            0b00001011001,
            0b00010110010,
            0b00101100100,
            0b01011001001,
        ])


if __name__ == '__main__':
    unittest.main()
