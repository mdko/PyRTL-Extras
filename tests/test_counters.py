import unittest
import pyrtl
from pyrtl.helperfuncs import formatted_str_to_val, val_to_formatted_str, val_to_signed_integer

import pyrtl_extras as pe


class TestCounters(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_counter(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.counter(reset, 4)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 20,
        })
        self.assertEqual(sim.tracer.trace['value'], [0] + list(range(16)) + list(range(4)))
        self.assertEqual(sim.tracer.trace['done'], [0] + [0]*15 + [1] + [0]*4)

    def test_gray_code_counter(self):
        reset = pyrtl.Input(1, "reset")
        i = pyrtl.Input(4, 'i')
        value, _done = pe.gray_code_counter(reset, i.bitwidth)
        pyrtl.probe(value, 'value')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 17,
            'i': [0] + list(range(16)) + [0],
        }, nsteps=18)
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
        # with open("gray_code_counter_pre.svg", "w") as f:
        #     pyrtl.output_to_svg(f)


class TestRTLRange(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_rtl_range_stop(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, 14)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 16,
        })
        self.assertEqual(sim.tracer.trace['value'], [0] + list(range(14)) + [13]*2)
        self.assertEqual(sim.tracer.trace['done'],  [0] * 14 + [1] * 3)

    def test_rtl_range_start_stop(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, 7, 15)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 10,
        })
        self.assertEqual(sim.tracer.trace['value'], [0] + list(range(7, 15)) + [14]*2)
        self.assertEqual(sim.tracer.trace['done'],  [0] * 8 + [1] * 3)

    def test_rtl_range_start_stop_step(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, 2, 13, 3)  # 2, 5, 8, 11, 11, 11, ...
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 8,
        })
        self.assertEqual(sim.tracer.trace['value'], [0, 2, 5, 8, 11, 11, 11, 11, 11])
        self.assertEqual(sim.tracer.trace['done'],  [0, 0, 0, 0,  1, 1, 1, 1, 1])

    def test_rtl_range_stop_negative_range(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, -8, -5)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 5,
        })
        self.assertEqual(
            sim.tracer.trace['value'],
            [0] + [pyrtl.formatted_str_to_val(x, 's' + str(value.bitwidth)) for x in [-8, -7, -6, -6, -6]]
        )
        self.assertEqual(sim.tracer.trace['done'],  [0] * 3 + [1] * 3)

    # Weird ones that should produce some sort of value equivalent to the empty list:

    def test_rtl_range_stop_negative_empty(self):
        # TODO fix
        # range(-5) == []
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, -5)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 2,
        })
        self.assertEqual(
            sim.tracer.trace['value'],
            [pyrtl.formatted_str_to_val(x, 's' + str(value.bitwidth)) for x in [0, -5, -5]]
        )
        self.assertEqual(sim.tracer.trace['done'],  [1, 1, 1])


    def test_rtl_range_start_stop_step_negative_empty(self):
        # TODO fix
        # range(-8, -5, -1) == []
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, -8, -5, -1)
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 3,
        })
        self.assertEqual(
            sim.tracer.trace['value'],
            [pyrtl.formatted_str_to_val(x, 's' + str(value.bitwidth)) for x in [0, -8, -8, -8]]
        )
        self.assertEqual(sim.tracer.trace['done'],  [1, 1, 1, 1])

    def test_rtl_range_start_stop_step_negative_range(self):
        reset = pyrtl.Input(1, "reset")
        value, done = pe.rtl_range(reset, -20, -32, -2)  # -20, -22, -24, -26, -28, -30, -30
        pyrtl.probe(value, 'value')
        pyrtl.probe(done, 'done')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'reset': [1] + [0] * 7,
        })
        self.assertEqual(
            sim.tracer.trace['value'],
            [pyrtl.formatted_str_to_val(x, 's' + str(value.bitwidth)) for x in [0, -20, -22, -24, -26, -28, -30, -30]]
        )
        self.assertEqual(sim.tracer.trace['done'],  [0, 0, 0, 0, 0, 0, 1, 1])

    # TODO test the range with wire inputs instead of ints

if __name__ == "__main__":
    unittest.main()
