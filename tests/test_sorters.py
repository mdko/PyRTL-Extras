import pyrtl
import unittest
import random
import itertools
import pyrtl_extras as pe

class TestBitonicSort(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def _run_test(self, nargs, bitwidth, signed=False, max_permutations=10):
        pyrtl.reset_working_block()
        ins = pyrtl.input_list([f'i{i}' for i in range(nargs)], bitwidth)
        outs = pe.bitonic_sort(*ins, signed=signed)
        for i, out in enumerate(outs):
            pyrtl.probe(out, f'o{i}')

        sim = pyrtl.Simulation()
        if signed:
            ivals = sorted([random.randrange(-2**(bitwidth-1), 2**(bitwidth-1)-1) for _ in range(len(ins))])
        else:
            ivals = sorted([random.randrange(0, 2**bitwidth-1) for _ in range(len(ins))])
        for ix, perm in enumerate(itertools.permutations(ivals)):

            v = lambda i: pyrtl.formatted_str_to_val(str(perm[i]), ('s' if signed else 'u') + str(bitwidth))
            sim.step({f'i{i}': v(i) for i in range(len(ins))})
            for i in range(len(outs)):
                v = sim.inspect(f'o{i}')
                v = pyrtl.val_to_signed_integer(v, bitwidth) if signed else v
                self.assertEqual(v, ivals[i])
            if ix >= max_permutations:
                break

    def test_bitonic_sort_1_nargs_8_bw_unsigned(self):
        self._run_test(1, 8)

    def test_bitonic_sort_2_nargs_8_bw_unsigned(self):
        self._run_test(2, 8)

    def test_bitonic_sort_4_nargs_8_bw_unsigned(self):
        self._run_test(4, 8)

    def test_bitonic_sort_8_nargs_8_bw_unsigned(self):
        self._run_test(8, 8)

    def test_bitonic_sort_16_nargs_8_bw_unsigned(self):
        self._run_test(16, 8)

    def test_bitonic_sort_0_raises_exception(self):
        with self.assertRaises(Exception) as ex:
            pe.bitonic_sort()
        self.assertEqual(str(ex.exception), 'bitonic_sort requires at least one argument to sort')

    def test_bitonic_sort_5_raises_exception(self):
        with self.assertRaises(Exception) as ex:
            self._run_test(5, 8)
        self.assertEqual(str(ex.exception), 'number of arguments to bitonic_sort must be a power of 2')

    def test_bitonic_sort_1_nargs_8_bw_signed(self):
        self._run_test(1, 8, signed=True)

    def test_bitonic_sort_2_nargs_8_bw_signed(self):
        self._run_test(2, 8, signed=True)

    def test_bitonic_sort_4_nargs_8_bw_signed(self):
        self._run_test(4, 8, signed=True)

    def test_bitonic_sort_8_nargs_8_bw_signed(self):
        self._run_test(8, 8, signed=True)

    def test_bitonic_sort_16_nargs_8_bw_signed(self):
        self._run_test(16, 8, signed=True)

if __name__ == "__main__":
    unittest.main()