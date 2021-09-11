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

    def test_signed_sub(self):
        i, j = pyrtl.input_list('i/4 j/4')
        o_u = i - j
        o_s = pe.signed_sub(i, j)
        pyrtl.probe(o_u, 'o_unsigned')
        pyrtl.probe(o_s, 'o_signed')
        sim = pyrtl.Simulation()
        i_vals = [pyrtl.formatted_str_to_val(x, 's4') for x in [-8, -8, -3,  2, 7, 2]]
        j_vals = [pyrtl.formatted_str_to_val(x, 's4') for x in [ 7, -8,  6, -4, 5, 4]]
        # These are fine if you have the 5th bit.
        # -8 - 7    = -15 = 0b1 0001 [overflow: adding two neg numbers leads to positive]  <<= diff. compared to just - (see 5th bit of output)
        # -8 - (-8) =   0 = 0b0 0000 [good]
        # -3 - 6    =  -9 = 0b1 0111 [overflow: adding two neg numbers leads to positive]  <<= diff. compared to just - (see 5th bit of output)
        #  2 - (-4) =   6 = 0b0 0110 <<= diff. compared to just - (see 5th bit of output)
        #  7 - 5    =   2 = 0b0 0010 [good]
        #  2 - 4 = 2 + (-4) = -2 0b0010 + 0b1100 = (0b1) 1110

        sim.step_multiple({
            'i': i_vals,
            'j': j_vals
        })
        # Why the difference? Because subtracting a value Y from X,
        # they are both treated as unsigned, so the result of - knows
        # nothing about the sign that it should use.
        self.assertEqual(
            sim.tracer.trace['o_unsigned'],
            [0b00001, 0b00000, 0b00111, 0b10110, 0b00010, 0b11110]
        )
        self.assertEqual(
            sim.tracer.trace['o_signed'],
            [0b10001, 0b00000, 0b10111, 0b00110, 0b00010, 0b11110]
        )
        # sim.tracer.render_trace(repr_per_name={
        #     'i': pe.binf(4, 5),
        #     'j': pe.binf(4, 5),
        #     'o_unsigned': pe.binf(5, 5),
        #     'o_signed': pe.binf(5, 5),
        # }, symbol_len=None
        # )

    def test_checked_sub(self):
        i, j = pyrtl.input_list('i/4 j/4')
        o, overflow = pe.checked_sub(i, j, 4)
        pyrtl.probe(o, 'o')
        pyrtl.probe(overflow, 'overflow')
        sim = pyrtl.Simulation()
        i_vals = [pyrtl.formatted_str_to_val(x, 's4') for x in [-8, -8, -3,  2, 7, 2]]
        j_vals = [pyrtl.formatted_str_to_val(x, 's4') for x in [ 7, -8,  6, -4, 5, 4]]
        sim.step_multiple({
            'i': i_vals,
            'j': j_vals
        })
        self.assertEqual(
            sim.tracer.trace['o'],
            [0b0001, 0b0000, 0b0111, 0b0110, 0b0010, 0b1110]
        )
        self.assertEqual(
            sim.tracer.trace['overflow'],
            [1, 0, 1, 0, 0, 0]
        )
        # sim.tracer.render_trace()

    def test_count_ones(self):
        i = pyrtl.Input(4, 'i')
        o = pe.count_ones(i)
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        inputs = range(16)
        sim.step_multiple({'i': inputs})
        self.assertEqual(
            sim.tracer.trace['o'],
            [bin(i)[2:].count('1') for i in inputs]
        )

    def test_count_zeroes(self):
        i = pyrtl.Input(4, 'i')
        o = pe.count_zeroes(i)
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        inputs = range(16)
        sim.step_multiple({'i': inputs})
        self.assertEqual(
            sim.tracer.trace['o'],
            [bin(i)[2:].zfill(4).count('0') for i in inputs]
        )

    def test_count_msb_zeroes(self):
        i = pyrtl.Input(8, 'i')
        o = pe.count_zeroes_from_end(i)
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'i': [0b00000001, 0b10010011, 0b00100000, 0b01100011, 0b11111111, 0b00000000]
        }, {
            'o': [         7,          0,          2,          1,          0,          8]
        })
        # sim.tracer.render_trace(repr_per_name={
        #     'i': pe.binf(8, 8)
        # }, symbol_len=None)

if __name__ == "__main__":
    unittest.main()
