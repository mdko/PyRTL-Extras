import collections
import operator
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

    Given a length n and length m WireVector the result of the
    signed subtraction is length max(n,m)+1. The inputs are twos
    complement sign extended to the same length before subtracting.
    If an integer is passed to either a or b, it will be converted
    automatically to a two's complemented constant.
    """
    if isinstance(a, int):
        a = pyrtl.Const(a, signed=True)
    if isinstance(b, int):
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
    return ~x + 1

def count_ones(w):
    """ Count the number of one bits in a wire """
    return reduce(operator.add, w)
    # Could also do this:
    return pyrtl.tree_reduce(operator.add, w)

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
