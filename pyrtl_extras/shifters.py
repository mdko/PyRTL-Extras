import pyrtl
import functools


def lfsr(seed, bitwidth, taps, func=lambda x, y: x ^ y):
    """ Linear-feedback shift register

    :param seed: initial value of the register
    :param bitwidth: length of the register (does *not* default to length of seed)
    :param taps: bitmask, or list of bit positions, indicating
        positions affecting the next state
    :param func: function to apply over the tapped bits, for
        determining value of bit to shift in; default is XOR
    :return: the value in the register
    """
    def bits_to_mask(bits):
        return functools.reduce(int.__or__, [2**i for i in bits])

    _, bw = pyrtl.infer_val_and_bitwidth(seed)
    if bw > bitwidth:
        raise pyrtl.PyrtlError('lfsr seed is too large for given bitwidth')

    reg = pyrtl.Register(bitwidth=bitwidth, reset_value=seed)
    if isinstance(taps, list):
        taps = bits_to_mask(taps)
    new_bit = pyrtl.tree_reduce(func, reg & taps)
    reg.next <<= pyrtl.concat(reg[:-1], new_bit)
    return reg
