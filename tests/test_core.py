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
        #o = pe.count_zeroes_from_end(i)  # Has same functionality
        o = pe.count_zeroes_from_end_fold(i)
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'i': [0b00000001, 0b10010011, 0b00100000, 0b01100011, 0b11111111, 0b00000000]
        })
        # sim.tracer.render_trace(repr_per_name={
        #     'i': pe.binf(8, 8)
        # }, symbol_len=None)
        self.assertEqual(
            sim.tracer.trace['o'],
            [7, 0, 2, 1, 0, 8]
        )

    def test_count_lsb_zeros(self):
        i = pyrtl.Input(8, 'i')
        #o = pe.count_zeroes_from_end(i, start='lsb')  # Has same functionality
        o = pe.count_zeroes_from_end_fold(i, start='lsb')
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        sim.step_multiple({
            'i': [0b00000001, 0b10010100, 0b00100000, 0b01100010, 0b11111111, 0b00000000]
        })
        # sim.tracer.render_trace(repr_per_name={
        #     'i': pe.binf(8, 8)
        # }, symbol_len=None)
        self.assertEqual(
            sim.tracer.trace['o'],
            [0, 2, 5, 1, 0, 8]
        )


class TestBits(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_get_single_bit(self):
        ix = pyrtl.Input(3, 'ix')
        c = pyrtl.Const("8'b10010011")
        o = pyrtl.Output(1, 'o')
        o <<= pe.rtl_index(c, ix)
        sim = pyrtl.Simulation()
        sim.step_multiple({'ix': range(7, -1, -1)})
        self.assertEqual(sim.tracer.trace['o'], [1, 0, 0, 1, 0, 0, 1, 1])

class TestRTLSlice(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_rtl_slice_returns_single_bit(self):
        ix = pyrtl.Input(4, 'ix')
        c = pyrtl.Const("8'b10010011")
        o = pyrtl.Output(1, 'o')
        o <<= pe.rtl_slice(c, ix, ix+1)
        sim = pyrtl.Simulation()
        sim.step_multiple({'ix': range(7, -1, -1)})
        self.assertEqual(sim.tracer.trace['o'], [1, 0, 0, 1, 0, 0, 1, 1])

    def test_rtl_slice_returns_range(self):
        start = pyrtl.Input(3, 'start')
        stop = pyrtl.Input(3, 'stop')
        c = pyrtl.Const("4'b1011")
        o = pyrtl.Output(4, 'o')
        o <<= pe.rtl_slice(c, start, stop)
        sim = pyrtl.Simulation()
        import itertools
        ranges = list([r for r in itertools.product(range(4), range(4)) if r[0] < r[1]])
        lefts = [r[0] for r in ranges]
        rights = [r[1] for r in ranges]
        sim.step_multiple({'start': lefts, 'stop': rights})
        expected = [int(("1101"[start:stop])[::-1], 2) for start, stop in ranges]
        self.assertEqual(sim.tracer.trace['o'], expected)

    def test_rtl_slice_integer_start(self):
        stop = pyrtl.Input(5, 'stop')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(0b11010010, 3, stop)
        sim = pyrtl.Simulation()
        sim.step_multiple({'stop': '45678'})
        self.assertEqual(sim.tracer.trace['o'], [0b0, 0b10, 0b010, 0b1010, 0b11010])

    def test_rtl_slice_with_integer_start_and_step_1(self):
        stop = pyrtl.Input(4, 'stop')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(0b11010110, 3, stop, 2)
        sim = pyrtl.Simulation()
        sim.step_multiple({'stop': '45678'})
        self.assertEqual(sim.tracer.trace['o'], [0b0, 0b0, 0b00, 0b00, 0b100])

    def test_rtl_slice_with_integer_start_and_step_2(self):
        stop = pyrtl.Input(4, 'stop')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(0b01101010, 3, stop, 2)
        sim = pyrtl.Simulation()
        sim.step_multiple({'stop': '45678'})
        self.assertEqual(sim.tracer.trace['o'], [0b1, 0b1, 0b11, 0b11, 0b011])

    def test_rtl_slice_with_integer_start_and_wire_step(self):
        stop = pyrtl.Input(5, 'stop')
        step = pyrtl.Const(3, signed=True)
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(0b01101010, 3, stop, step)
        sim = pyrtl.Simulation()
        sim.step_multiple({'stop': '45678'})
        self.assertEqual(sim.tracer.trace['o'], [0b1, 0b1, 0b1, 0b11, 0b011])

    def test_rtl_slice_all_wire_arguments(self):
        o = pe.rtl_slice(
            pyrtl.Const(0b10110010),
            pyrtl.Const(2, signed=True),  # start (inclusive)
            pyrtl.Const(8, signed=True),  # end (exclusive)
            pyrtl.Const(3, signed=True)   # step
        )
        pyrtl.probe(o, 'o')
        sim = pyrtl.Simulation()
        sim.step({})
        self.assertEqual(sim.tracer.trace['o'], [0b10])

    def test_rtl_slice_integer_start_end_and_step(self):
        import warnings
        value = 0b11010110
        start = 3
        stop = 7
        step = 2
        o = pyrtl.Output(8, 'o')
        for args in ((start,), (start, stop), (start, stop, step)):
            with warnings.catch_warnings(record=True) as w:
                o <<= pe.rtl_slice(value, *args)
            self.assertEqual(
                str(w[0].message),
                "Integer values (or defaults) were provided as the start and end indices "
                "and step to `rtl_slice()`. Consider using standard slicing notation instead: `w[start:stop:step]`."
            )

    def test_rtl_slice_negative_start_various_hardcoded(self):
        value = pyrtl.Const(0b10011100)
        start = pyrtl.Input(5, 'start')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(value, start, None, None)
        sim = pyrtl.Simulation()

        sim.step({'start': pyrtl.formatted_str_to_val(str(-1), 's5')})
        self.assertEqual(sim.inspect('o'), 0b1)  # just bit 7

        sim.step({'start': pyrtl.formatted_str_to_val(str(-2), 's5')})
        self.assertEqual(sim.inspect('o'), 0b10)  # bits 7, 6

        sim.step({'start': pyrtl.formatted_str_to_val(str(-3), 's5')})
        self.assertEqual(sim.inspect('o'), 0b100)  # bits 7, 6, 5

        sim.step({'start': pyrtl.formatted_str_to_val(str(-4), 's5')})
        self.assertEqual(sim.inspect('o'), 0b1001)  # bits 7, 6, 5, 4

        sim.step({'start': pyrtl.formatted_str_to_val(str(-5), 's5')})
        self.assertEqual(sim.inspect('o'), 0b10011)  # bits 7, 6, 5, 4, 3

        sim.step({'start': pyrtl.formatted_str_to_val(str(-6), 's5')})
        self.assertEqual(sim.inspect('o'), 0b100111)  # bits 7, 6, 5, 4, 3, 2

        sim.step({'start': pyrtl.formatted_str_to_val(str(-7), 's5')})
        self.assertEqual(sim.inspect('o'), 0b1001110)  # bits 7, 6, 5, 4, 3, 2, 1

        sim.step({'start': pyrtl.formatted_str_to_val(str(-8), 's5')})
        self.assertEqual(sim.inspect('o'), 0b10011100)  # bits 7, 6, 5, 4, 3, 2, 1, 0

        # rest should behave the same as step=-8
        for v in range(-9, -16):
            sim.step({'start': pyrtl.formatted_str_to_val(str(v), 's5')})
            self.assertEqual(sim.inspect('o'), 0b10011100)  # bits 7, 6, 5, 4, 3, 2, 1, 0

    def test_rtl_slice_negative_start_n(self):
        start = pyrtl.Input(5, 'start')
        o = pyrtl.Output(16, 'o')
        v = pyrtl.Const(0b1101011000101001, name='v')
        o <<= pe.rtl_slice(v, start, None, None)
        sim = pyrtl.Simulation()
        for s in range(-16, 0):
            sim.step({'start': pyrtl.formatted_str_to_val(str(s), 's' + str(start.bitwidth))})
            self.assertEqual(sim.inspect('o'), int(bin(v.val)[2:].zfill(o.bitwidth)[::-1][s::][::-1], 2))

    def test_rtl_slice_negative_end_various_hardcoded(self):
        value = pyrtl.Const(0b10011101)
        stop = pyrtl.Input(5, 'stop')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(value, None, stop, None)
        sim = pyrtl.Simulation()

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-1), 's5')})
        self.assertEqual(sim.inspect('o'), 0b0011101)  # bits 0, 1, 2, 3, 4, 5, 6

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-2), 's5')})
        self.assertEqual(sim.inspect('o'), 0b011101)  # bits 0, 1, 2, 3, 4, 5

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-3), 's5')})
        self.assertEqual(sim.inspect('o'), 0b11101)  # bits 0, 1, 2, 3, 4

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-4), 's5')})
        self.assertEqual(sim.inspect('o'), 0b1101)  # bits 0, 1, 2, 3

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-5), 's5')})
        self.assertEqual(sim.inspect('o'), 0b101)  # bits 0, 1, 2

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-6), 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)  # bits 0, 1

        sim.step({'stop': pyrtl.formatted_str_to_val(str(-7), 's5')})
        self.assertEqual(sim.inspect('o'), 0b1)  # bits 0

        # TODO >= -8 would return an empty list in normal Python
        # for v in range(-8, -16):
        #     sim.step({'stop': pyrtl.formatted_str_to_val(str(v), 's5')})
        #     self.assertEqual(sim.inspect('o'), ...)

    def test_rtl_slice_negative_step_1(self):
        # Basically just reverses...
        i = pyrtl.Input(8, 'i')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(i, None, None, pyrtl.Const(-1, signed=True))
        sim = pyrtl.Simulation()
        for v in range(0, i.bitmask + 1):
            sim.step({'i': v})
            self.assertEqual(sim.inspect('o'), int(bin(v)[2:].zfill(o.bitwidth)[::-1], 2))

    def test_rtl_slice_negative_step_2(self):
        i = pyrtl.Input(8, 'i')
        o = pyrtl.Output(8, 'o')
        o <<= pe.rtl_slice(i, None, None, pyrtl.Const(-2, signed=True))
        sim = pyrtl.Simulation()
        for v in range(0, i.bitmask + 1):
            sim.step({'i': v})
            self.assertEqual(sim.inspect('o'), int(bin(v)[2:].zfill(o.bitwidth)[::2][::-1], 2))

    def test_rtl_slice_negative_various_hardcoded(self):
        # Easier to visualize, though the next test does the same thing
        # with fewer lines.
        step = pyrtl.Input(5, 'step')
        o = pyrtl.Output(16, 'o')
        v = pyrtl.Const(0b1101011000101001, name='v')
        o <<= pe.rtl_slice(v, None, None, step)
        sim = pyrtl.Simulation()

        sim.step({'step': pyrtl.formatted_str_to_val('-1', 's5')})
        self.assertEqual(sim.inspect('o'), 0b1001010001101011)

        sim.step({'step': pyrtl.formatted_str_to_val('-2', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01101001)

        sim.step({'step': pyrtl.formatted_str_to_val('-3', 's5')})
        self.assertEqual(sim.inspect('o'), 0b110111)

        sim.step({'step': pyrtl.formatted_str_to_val('-4', 's5')})
        self.assertEqual(sim.inspect('o'), 0b1001)

        sim.step({'step': pyrtl.formatted_str_to_val('-5', 's5')})
        self.assertEqual(sim.inspect('o'), 0b1111)

        sim.step({'step': pyrtl.formatted_str_to_val('-6', 's5')})
        self.assertEqual(sim.inspect('o'), 0b111)

        sim.step({'step': pyrtl.formatted_str_to_val('-7', 's5')})
        self.assertEqual(sim.inspect('o'), 0b001)

        sim.step({'step': pyrtl.formatted_str_to_val('-8', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)

        sim.step({'step': pyrtl.formatted_str_to_val('-9', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)

        sim.step({'step': pyrtl.formatted_str_to_val('-10', 's5')})
        self.assertEqual(sim.inspect('o'), 0b11)

        sim.step({'step': pyrtl.formatted_str_to_val('-11', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)

        sim.step({'step': pyrtl.formatted_str_to_val('-12', 's5')})
        self.assertEqual(sim.inspect('o'), 0b11)

        sim.step({'step': pyrtl.formatted_str_to_val('-13', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)

        sim.step({'step': pyrtl.formatted_str_to_val('-14', 's5')})
        self.assertEqual(sim.inspect('o'), 0b01)

        sim.step({'step': pyrtl.formatted_str_to_val('-15', 's5')})
        self.assertEqual(sim.inspect('o'), 0b11)

    def test_rtl_slice_negative_step_n(self):
        step = pyrtl.Input(5, 'step')
        o = pyrtl.Output(16, 'o')
        v = pyrtl.Const(0b1101011000101001, name='v')
        o <<= pe.rtl_slice(v, None, None, step)
        sim = pyrtl.Simulation()
        for s in range(-16, 0):
            sim.step({'step': pyrtl.formatted_str_to_val(str(s), 's' + str(step.bitwidth))})
            self.assertEqual(sim.inspect('o'), int(bin(v.val)[2:].zfill(o.bitwidth)[::-s][::-1], 2))

    def test_rtl_slice_invalid_number_of_arguments(self):
        c = pyrtl.Const("8'b10010011")
        with self.assertRaises(pyrtl.PyrtlError) as ex:
            _o = pe.rtl_slice(c)
        self.assertEqual(
            str(ex.exception),
            "rtl_slice takes 1 argument (stop), 2 arguments (start, stop), "
            "or 3 arguments (start, stop, step)."
        )


class TestHelpers(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_bitwidth_for_index(self):
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(2)), 1)  # bits 0 - 1
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(3)), 2)  # bits 0 - 2
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(4)), 2)  # bits 0 - 3
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(5)), 3)  # bits 0 - 4
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(6)), 3)  # bits 0 - 5
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(7)), 3)  # bits 0 - 6
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(8)), 3)  # bits 0 - 7
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(9)), 4)  # bits 0 - 8
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(15)), 4)  # bits 0 - 14
        self.assertEqual(pe.bitwidth_for_index(pyrtl.WireVector(16)), 4)  # bits 0 - 15

    def test_negate(self):
        i = pyrtl.Input(8, 'i')
        o = pyrtl.Output(name='o')
        o <<= pe.negate(i)
        sim = pyrtl.Simulation()
        for v in range(-128, 128):
            sim.step({
                'i': pyrtl.formatted_str_to_val(str(v), 's8')
            })
            self.assertEqual(pyrtl.val_to_signed_integer(sim.inspect('o'), o.bitwidth), -v)

if __name__ == "__main__":
    unittest.main()
