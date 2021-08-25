import pyrtl
from pyrtl.helperfuncs import infer_val_and_bitwidth
from pyrtl.pyrtlexceptions import PyrtlError

from .core import gray_code


def counter(reset, bitwidth=None, max=None, init=0, wrap_on_overflow=True):
    """ Standard counter that counts up.

    :param reset: condition to reset the counter
    :param bitwidth: size of the counter. If not specified, it will be inferred
        from the value of `max`. Either `bitwidth` or `max` must be specified.
    :param max: max value; if None, the counter will count up to 2^`bitwidth`-1,
        wrapping around if `wrap_on_overflow` is True. Needs to fit in bitwidth bits,
        if `bitwidth` is specified. Either `bitwidth` or `max` must be specified.
    :param init: initial value of the counter (defaults to 0)
    :param wrap_on_overflow: if True, the counter will wrap around when it reaches max
        (if `max` is not None) or 2^`bitwidth`-1 (if `max` is None).
    :return: the counter's current value, and if the current value equals the maximum
        (either `max` or 2^`bitwidth`-1)

    Implication from all this: if init > max_value and wrap_on_overflow is False, the
    counter will do nothing.
    """
    if bitwidth is None and max is None:
        raise PyrtlError("Either bitwidth or max value must be supplied")
    if max is not None:
        _, bw = infer_val_and_bitwidth(max)[1]
        if bitwidth is None:
            bitwidth = bw
        elif bitwidth < bw:
            raise PyrtlError("max value does not fit in bitwidth")
    else:
        max = 2 ** bitwidth - 1

    cnt = pyrtl.Register(bitwidth=bitwidth)
    with pyrtl.conditional_assignment:
        with reset:
            cnt.next |= init
        with cnt < max:
            cnt.next |= cnt + 1
        with (cnt == max) & wrap_on_overflow:
            cnt.next |= 0
    return cnt


def down_counter(bitwidth, start, reset):
    raise NotImplementedError("down_counter is not implemented yet")


def gray_code_counter(reset, bitwidth):
    """ A counter that counts in a Gray code.

    :param reset: condition to reset the counter
    param bitwidth: size of the counter
    :return: the counter value
    """
    reset = pyrtl.as_wires(reset)
    count = counter(reset, bitwidth)
    return gray_code(count)
