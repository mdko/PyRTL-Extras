import unittest
import pyrtl

import pyrtl_extras as pe


class TestCore(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_gray_code_encoder_4_bits(self):
        i = pyrtl.Input(4, 'i')
        o = pe.gray_code(i)
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        sim.step_multiple({'i': range(16)})
        self.assertEqual(sim.tracer.trace['o'], [
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
        ])
        # pyrtl.synthesize()
        # pyrtl.optimize()
        # print(len(pyrtl.working_block().logic_subset(op='&|^~')))
        # with open("gray_code_test_2.svg", "w") as f:
        #     pyrtl.output_to_svg(f)


if __name__ == "__main__":
    unittest.main()
