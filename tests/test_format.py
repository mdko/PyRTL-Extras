import unittest
import six
import pyrtl
import pyrtl_extras as pe

class TestFormat(unittest.TestCase):
    def setUp(self):
        pyrtl.reset_working_block()

    def test_print_memory(self):
        i = pyrtl.Input(8, 'i')
        mem = pyrtl.MemBlock(bitwidth=32, addrwidth=8, name='mem')
        pyrtl.probe(mem[i], 'o')
        sim = pyrtl.Simulation(memory_value_map={
            mem: {i: i*10 for i in range(2**8)}
        })
        io = six.StringIO()
        pe.print_memory(sim, mem, addr=0, count=16, file=io)
        print(io.getvalue())
        # TODO fix the formatting so there are no spaces at the end of the lines
        self.assertEqual(
            io.getvalue(),
            "0x00: 0x0           0xa           0x14          0x1e    \n"
            "0x04: 0x28          0x32          0x3c          0x46    \n"
            "0x08: 0x50          0x5a          0x64          0x6e    \n"
            "0x0c: 0x78          0x82          0x8c          0x96          "
        )

if __name__ == "__main__":
    unittest.main()
