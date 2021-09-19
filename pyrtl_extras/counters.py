import pyrtl
from pyrtl.helperfuncs import infer_val_and_bitwidth
from pyrtl.pyrtlexceptions import PyrtlError

from .core import gray_code

def _base_counter(reset, bitwidth, start, stop, step, wrap):
    """
    :param reset:
    :param bitwidth:
    :param start: inclusive
    :param stop: exclusive
    :param step:
    :param wrap:
    """
    # TODO insert some checks to make sure the values are reasonable
    reset, wrap = pyrtl.as_wires(reset), pyrtl.as_wires(wrap)

    cnt = pyrtl.Register(bitwidth=bitwidth)
    done = (cnt + step) >= stop
    with pyrtl.conditional_assignment:
        with reset:
            cnt.next |= start
        with ~done:
            cnt.next |= cnt + step
        with wrap:
            cnt.next |= start
    return cnt, done

def rtl_range(reset, start, stop, step=1):
    """ A counter that counts in a range (akin to the normal range function in Python).

    :param reset: when to reset (i.e. "start") the counter
    :param start: the starting value of the counter (inclusive)
    :param stop: the stopping value of the counter (exclusive)
    :param step: the step size of the counter (defaults to 1)
    :return Tuple[Wire, Wire]: the counter value, and whether the current value is the
        highest it can be without exceeding the stopping value (i.e. if it's "done" counting)

    This saturates, meaning it will stay at the stop value once reached.
    """
    if start > stop:
        raise PyrtlError("start value must be less than or equal to stop value")
    if start < 0:
        raise PyrtlError("start value must be greater than or equal to 0")
    if stop < 0:
        raise PyrtlError("stop value must be greater than or equal to 0")

    _, bw = infer_val_and_bitwidth(stop)
    return _base_counter(reset, bw, start, stop, step, False)

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
    :return Tuple[Wire, Wire]: the counter's current value, and whether the current value
        equals the maximum (either `max` or 2^`bitwidth`-1) (i.e. if it's "done" counting)

    Implication from all this: if init > max and wrap_on_overflow is False, the
    counter will do nothing.
    """
    if bitwidth is None and max is None:
        raise PyrtlError("Either bitwidth or max value must be supplied")
    if max is not None:
        _, bw = infer_val_and_bitwidth(max)
        if bitwidth is None:
            bitwidth = bw
        elif bitwidth < bw:
            raise PyrtlError("max value does not fit in bitwidth")
    else:
        assert bitwidth is not None
        max = 2 ** bitwidth - 1

    # max + 1 because the stop value is inclusive
    return _base_counter(reset, bitwidth, init, max + 1, 1, wrap_on_overflow)

def down_counter(reset, bitwidth=None, init=None, min=0, wrap_on_underflow=True):
    """ Counter that counts down.

    :param reset: condition to reset the counter
    :param bitwidth: size of the counter. If not specified, it will be inferred
        from the value of `init`. Either `bitwidth` or `init` must be specified.
    :param init: initial value of the counter (defaults to 2^`bitwidth`-1). Needs to
        fit in bitwidth bits, if `bitwidth` is specified. Either `bitwidth` or `init`
        must be specified.
    :param min: min value; if None, the counter will count down to 0,
        wrapping around if `wrap_on_underflow` is True.
    :param wrap_on_underflow: if True, the counter will wrap around when it reaches min.
    :return Tuple[Wire, Wire]: the counter's current value, and whether the current value
        equals the minimum (either `min` or 0) (i.e. if it's "done" counting)

    Implication from all this: if init < min and wrap_on_underflow is False, the
    counter will do nothing.
    """
    if bitwidth is None and init is None:
        raise PyrtlError("Either bitwidth or init value must be supplied")
    if init is not None:
        _, bw = infer_val_and_bitwidth(init)
        if bitwidth is None:
            bitwidth = bw
        elif bitwidth < bw:
            raise PyrtlError("init value does not fit in bitwidth")
    else:
        assert bitwidth is not None
        init = 2 ** bitwidth - 1

    # TODO check how min is used, since exclusive
    # TODO change + in _base_counter to signed_add?
    return _base_counter(reset, bitwidth, init, min, -1, wrap_on_underflow)


def gray_code_counter(reset, bitwidth):
    """ A counter that counts in a Gray code.

    :param reset: condition to reset the counter
    param bitwidth: size of the counter
    :return: the counter value
    """
    reset = pyrtl.as_wires(reset)
    count, done = counter(reset, bitwidth)
    return gray_code(count), done
