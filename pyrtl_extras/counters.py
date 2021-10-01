import pyrtl
from pyrtl.pyrtlexceptions import PyrtlError

from .core import gray_code

# def rtl_range(reset, start=0, stop=None, step=1, wrap=False):
# Use *args to emulate signature of normal Python range
# TODO emit done on same cycle if `range(...)` would be empty
# TODO determine if first cycle of counting should be on reset, or cycle after it
# TODO connect with (or at least document) how to connect it to ready-valid
def rtl_range(reset, *args, wrap=False):
    """ A counter that counts in a range.

    Signatures::

        rtl_range(reset, stop, wrap=False)
        rtl_range(reset, start, stop[, step], wrap=False)

    :param reset: when to reset (i.e. "start") the counter
    :param start: the starting value of the counter (inclusive)
    :param stop: the stopping value of the counter (exclusive)
    :param step: the step size of the counter (defaults to 1)
    :param wrap: if True, the counter will wrap around when it reaches the maximum/minimum
        (depending on direction of counting)
    :return Tuple[Wire, Wire]: the counter value, and whether the current value is the
        highest it can be without exceeding the stopping value (i.e. if it's "done" counting)

    Protocol notes: The last value produced by rtl_range() is produced on the same cycle `done` goes high
    for the first time. `done` stays high until `reset` is asserted again. If `done` is calculated
    to be high at the same time `reset` is asserted high, that means there is nothing in the range.

    This should generally behave like a normal Python `range` function, with the exception
    of needing a `reset` wire to know when to reset (i.e. start) the counter. So it should
    work with a wide variety of start/stop/step values, including negative numbers.

    If step is a wire and is has a zero value at the same time as `reset` is high,
    weird things may happen (this would be a ValueError in a normal python `range()` call).

    """
    start, step = 0, 1
    if len(args) == 1:
        stop = args[0]
    elif len(args) == 2:
        start, stop = args
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise PyrtlError(
            "rtl_range takes 1 argument (stop), 2 arguments (start, stop), "
            "or 3 arguments (start, stop, step)."
        )

    start = pyrtl.as_wires(start, signed=True)
    stop = pyrtl.as_wires(stop, signed=True)
    step = pyrtl.as_wires(step, signed=True)
    reset = pyrtl.as_wires(reset)
    wrap = pyrtl.as_wires(wrap)

    if isinstance(step, pyrtl.Const) and step.val == 0:
        raise pyrtl.PyrtlError("step value must be non-zero")

    bitwidth = max(start.bitwidth, stop.bitwidth)
    cnt = pyrtl.Register(bitwidth=bitwidth)
    cnt_next = pyrtl.signed_add(cnt, step)

    done = pyrtl.WireVector(bitwidth=1)
    with pyrtl.conditional_assignment:
        # NOTE: We need to check for reset so we don't mistakenly signal we're done
        # before we've even started. Note that this creates a combinational dependency
        # between reset and done, which may not be acceptable (i.e. to-port/from-port).
        # A possible other way to handle this would be to have a separate register for
        # the "started" and use that for determining this. The main issue that is trying
        # to solve is comparing the value of cnt before it has been properly initialized.
        # TODO maybe add with ~reset:
        with pyrtl.signed_gt(step, 0):
            # Going up
            done |= pyrtl.signed_ge(cnt_next, stop)
        with pyrtl.signed_lt(step, 0):
            # Going down
            done |= pyrtl.signed_le(cnt_next, stop)

    with pyrtl.conditional_assignment:
        with reset:
            cnt.next |= start
        with ~done:
            cnt.next |= cnt_next
        with wrap:
            cnt.next |= start
    return cnt, done

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
        _, bw = pyrtl.infer_val_and_bitwidth(max, signed=True)
        if bitwidth is None:
            bitwidth = bw
        elif bitwidth < bw:
            raise PyrtlError("max value does not fit in bitwidth")
    else:
        assert bitwidth is not None
        max = 2 ** bitwidth - 1

    # max + 1 because the stop value is inclusive
    return rtl_range(reset, init, max + 1, 1, wrap=wrap_on_overflow)

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
        _, bw = pyrtl.infer_val_and_bitwidth(init)
        if bitwidth is None:
            bitwidth = bw
        elif bitwidth < bw:
            raise PyrtlError("init value does not fit in bitwidth")
    else:
        assert bitwidth is not None
        init = 2 ** bitwidth - 1

    # min - 1 because the stop value is exclusive
    return rtl_range(reset, init, min-1, -1, wrap=wrap_on_underflow)


def gray_code_counter(reset, bitwidth):
    """ A counter that counts in a Gray code.

    :param reset: condition to reset the counter
    param bitwidth: size of the counter
    :return: the counter value
    """
    reset = pyrtl.as_wires(reset)
    count, done = counter(reset, bitwidth)
    return gray_code(count), done
