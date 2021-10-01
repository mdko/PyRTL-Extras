import collections
from logging import warn
import operator
import math
import six
from functools import reduce
import pyrtl


def gray_code(n):
    """ Get the binary-reflected gray code of n """
    n = pyrtl.as_wires(n)
    return n ^ n[1:]

def signed_sub(a, b):
    """ Return a WireVector for result of signed subtraction.

    :param a: a WireVector to serve as first input to subtraction
    :param b: a WireVector to serve as second input to subtraction

    Given a length n WireVector and length m WireVector the result of the
    signed subtraction is length max(n,m)+1. The inputs are twos
    complement sign extended to the same length before subtracting.
    If an integer is passed to either a or b, it will be converted
    automatically to a two's complemented constant.
    """
    if isinstance(a, (int, six.string_types)):
        a = pyrtl.Const(a, signed=True)
    if isinstance(b, (int, six.string_types)):
        b = pyrtl.Const(b, signed=True)
    a, b = pyrtl.match_bitwidth(pyrtl.as_wires(a), pyrtl.as_wires(b), signed=True)
    result_len = len(a) + 1
    ext_a = a.sign_extended(result_len)
    ext_b = b.sign_extended(result_len)
    # add and truncate to the correct length
    return (ext_a - ext_b)[0:result_len]

CheckedResult = collections.namedtuple('CheckedResult', ['result', 'overflow'])

def checked_sub(a, b, bitwidth):
    res = signed_sub(a, b).truncate(bitwidth)
    # TODO All of these use subtraction under the hood, so this is less 'efficient'
    # then we really need, given that we're also doing subtraction in signed_sub.
    # Probably better to just have one function that does it all.
    cond1 = pyrtl.signed_ge(a, 0) & pyrtl.signed_lt(b, 0) & pyrtl.signed_lt(res, 0)
    cond2 = pyrtl.signed_lt(a, 0) & pyrtl.signed_ge(b, 0) & pyrtl.signed_ge(res, 0)
    return CheckedResult(res, cond1 | cond2)

def difference(x, y):
    """ Returns max(x, y) - min(x, y) [taking signedness into account] """
    # Doing this verbosely because I only want one call to signed_sub.
    x_gt_y = pyrtl.signed_gt(x, y)
    h = pyrtl.select(x_gt_y, x, y)
    l = pyrtl.select(x_gt_y, y, x)
    return signed_sub(h, l)

def negate(x):
    """ Negate a number (a la twos complement), not invert """
    # Use this to automatically get correct size out (~x + 1 doesn't get it automatically)
    return signed_sub(0, x)

def count_ones(w):
    """ Count the number of one bits in a wire """
    return reduce(operator.add, w)
    # Could also do this:
    #return pyrtl.tree_reduce(operator.add, w)

def count_zeroes(w):
    return len(w) - count_ones(w)

# Two versions of the same function:
#   - count_zeroes_from_end_fold()
#   - count_zeroes_from_end()
# Both are here just to see difference in programming complexity and generated netlist complexity

def count_zeroes_from_end_fold(x, start='msb'):
    def f(accum, x):
        found, count = accum
        is_zero = x == 0
        to_add = ~found & is_zero
        count = count + to_add
        return (found | ~is_zero, count)
    l = x[::-1] if start == 'msb' else x
    return reduce(f, l, (pyrtl.as_wires(False), 0))[1]

# NOTE: this is essentially a fold, so we could probably use the stdlib's functools.reduce function (see above)
def count_zeroes_from_end(x, start='msb'):
    if start not in ('msb', 'lsb'):
        raise pyrtl.PyrtlError('Invalid start parameter')

    def _count(x, found):
        end = x[-1] if start == 'msb' else x[0]
        is_zero = end == 0
        to_add = ~found & is_zero
        if len(x) == 1:
            return to_add
        else:
            rest = x[:-1] if start == 'msb' else x[1:]
            rest_to_add = _count(rest, found | ~is_zero)
            return to_add + rest_to_add
    return _count(x, pyrtl.as_wires(False))

def bitwidth_for_index(w):
    """ Returns the number of bits needed to index every bit of w.

    :param w: the wire being indexed into
    :return: the number of bits needed to index every bit of w

    Examples::

        0bx requires a 1 bit index wv (index bit 0 only)
        0bxx requires a 1 bit index wv (index bit 0 and 1)
        0bxxx requires a 2 bit index wv (index bits 0, 1, and 2)
        0bxxxx requires a 2 bit index wv (index bits 0, 1, 2, and 3)
        0bxxxxx requires a 3 bit index wv (index bits 0, 1, 2, 3, and 4)
        0bxxxxxx requires a 3 bit index wv (index bits 0, 1, 2, 3, 4, and 5)
    """
    return int(math.floor(math.log2(w.bitwidth - 1)) + 1)

def rtl_index(w, ix):
    """

    Like doing `w[ix]`
    """
    return pyrtl.shift_right_logical(w, ix)[0]
    # Could also do this:
    #return rtl_slice(w, ix, ix+1)

def rtl_slice(w, *args):
    """ Slice into a WireVector using WireVectors as the start (optional), end, and step (optional) values.

    Signatures::

        rtl_slice(w, stop)
        rtl_slice(w, start, stop[, step])

    :param w: the WireVector or int to index into.
    :param start: the starting value of the counter, inclusive (default: 0)
    :param stop: the stopping value of the counter, exclusive (default: len(w))
    :param step: the step size of the counter (default: 1); this will be treated
        as *signed* if a WireVector
    :return: a slice of the original WireVector, i.e. a subsection of the
        original wire, possibly with some skipped bits depending on the value of step.
        The width of the slice totally depends on the argument values.

    It's probably easiest to think of calling `rtl_slice(w, start, end, step)`
    as being equivalent to `w[start:end:step]` or `w[slice(start, end, step)]`.

    This function is used to overcome the (very reasonable) limitation that PyRTL imposes on
    slicing a WireVector: that the slice indices meet the same constraints as normal Python
    slices.

    Needing to use wires as indices is typically a sign that the object you're
    indexing into should be a memory, but this function is provided for experimentation
    nonetheless. Note that this will create a large series of muxes.

    Also note that it is an error for step to be 0; we currently don't report this error
    (instead just returning a 0 wire), but this function might be changed to return an
    error wire indicating such an occurence instead.

    There are no requirements on the bitwidth of step.

    Example::

        rtl_slice(
            pyrtl.Const(0b10110010),
            pyrtl.Const(2),  # start (inclusive)
            pyrtl.Const(8),  # end (exclusive)
            pyrtl.Const(3)   # step
        ) == 0b10
        
        From...
         end (exclusive) to...
         |     start (inclusive)
         |     |
         v     v
        0b10110010
            ^  ^
            |  |
        get every 3rd bit, and concatenate to, get 0b10
    """

    # TODO handle if negative, like normal slices allow

    w = pyrtl.as_wires(w)

    start, stop, step = None, None, None
    if len(args) == 1:
        stop = args[0]
    elif len(args) == 2:
        start, stop = args
    elif len(args) == 3:
        start, stop, step = args
    else:
        raise pyrtl.PyrtlError(
            "rtl_slice takes 1 argument (stop), 2 arguments (start, stop), "
            "or 3 arguments (start, stop, step)."
        )

    if start is None:
        start = 0
    if stop is None:
        stop = w.bitwidth
    if step is None:
        step = 1

    if all(isinstance(x, int) for x in (start, stop, step)):
        import warnings
        warnings.warn(
            "Integer values (or defaults) were provided as the start and end indices "
            "and step to `rtl_slice()`. Consider using standard slicing notation instead: "
            "`w[start:stop:step]`."
        )

    # Instead of just making them all wires via as_wires,
    # we can be smarter and more efficient by using slice nets when possible.
    if isinstance(start, int):
        w = w[start:]
    else:
        w = pyrtl.shift_right_logical(w, start)

    if isinstance(stop, int):
        w = w[:stop]
    else:
        count = stop - start
        mask = pyrtl.shift_left_logical(pyrtl.Const(1, w.bitwidth), count) - 1
        w = w & mask

    if isinstance(step, int):
        w = w[::step]  # ValueError if step is 0
    else:
        # From here...
        wn = pyrtl.WireVector(w.bitwidth)
        stepn = pyrtl.WireVector(step.bitwidth)

        with pyrtl.conditional_assignment:
            with pyrtl.signed_lt(step, 0):
                stepn |= negate(step)
                wn |= w[::-1]
            with pyrtl.otherwise:
                stepn |= step
                wn |= w
        # ...to here is for dealing with negative step values. It's highly experimental :)

        stepn = stepn if 2**stepn.bitwidth >= wn.bitwidth else stepn.zero_extended(bitwidth_for_index(wn))
    
        w = pyrtl.mux(
            stepn,
            pyrtl.Const(0),  # A step of 0 is invalid; report that with error line later
            *[wn[::s] for s in range(1, wn.bitwidth)],
            default=wn[0].zero_extended(wn.bitwidth)  # any step > w.bitwidth is just first bit
        )

    return w