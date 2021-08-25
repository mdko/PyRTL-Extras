import unittest
import pyrtl

import pyrtl_extras as pe


class TestCounters(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_counter(self):
        reset = pyrtl.Input(1, "reset")
        value = pe.counter(reset, 4)
        pyrtl.probe(value, 'value')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 20,
        })
        # sim.tracer.render_trace()
        self.assertEqual(sim.tracer.trace['value'], [0] + list(range(16)) + list(range(4)))

    def test_gray_code_counter(self):
        reset = pyrtl.Input(1, "reset")
        i = pyrtl.Input(4, 'i')
        value = pe.gray_code_counter(reset, i.bitwidth)
        pyrtl.probe(value, 'value')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 17,
            'i': [0] + list(range(16)) + [0],
        }, nsteps=18)
        # sim.tracer.render_trace()
        self.assertEqual(sim.tracer.trace['value'], [
            0b0000,
            0b0000,
            0b0001,
            0b0011,
            0b0010,
            0b0110,
            0b0111,
            0b0101,
            0b0100,
            0b1100,
            0b1101,
            0b1111,
            0b1110,
            0b1010,
            0b1011,
            0b1001,
            0b1000,
            0b0000,
        ])
        # pyrtl.synthesize()
        # pyrtl.optimize()
        # print(len(pyrtl.working_block().logic_subset(op='&|^~')))
        with open("gray_code_counter_pre.svg", "w") as f:
            pyrtl.output_to_svg(f)


if __name__ == "__main__":
    unittest.main()
