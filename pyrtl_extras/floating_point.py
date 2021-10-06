import pyrtl
import math

from .core import signed_sub, negate, count_zeroes_from_end

# TODO subnormal numbers?
# TODO fix and test for the fp_to_float/float_to_fp with negative numbers

_Exponent_bits = {
    'half': 5,
    'single': 8,
    'double': 11,
    'quad': 15,
}

# These are the explicitly stored bits, since
# really the #bits significand = 1 + #bits fraction.
_Fraction_bits = {
    'half': 10,
    'single': 23,
    'double': 52,
    'quad': 112,
}

_Bias = {
    'half': 15,  # 2 ** (_Exponent_bits['half'] - 1) - 1
    'single': 127,
    'double': 1023,
    'quad': 16383,
}

_Bitwidth = {
    'half': 16,  # 1 + _Exponent_bits['half'] + _Fraction_bits['half']
    'single': 32,
    'double': 64,
    'quad': 128,
}


def float_in_range(x, precision):
    if precision not in ('half', 'single', 'double', 'quad'):
        raise ValueError("Precision must be one of 'half', 'single', 'double', or 'quad'")
    smallest = 2 ** (1 - _Bias[precision])
    largest = (2 ** (2 ** _Exponent_bits[precision] - _Bias[precision] - 2)) *\
              (2 - (1 / (2 ** _Fraction_bits[precision])))
    return abs(x) >= smallest and abs(x) <= largest


def zfill_right(x, n):
    return x + '0' * (n - len(x))


def float_to_fp(x, precision='single'):
    """ Convert the Python float into an integer,
        whose bitpattern represents the floating point number.

    :param x:
    :param precision:
    :return:
    """

    # Zero
    if x == 0:
        return 0

    # Inf
    if math.isinf(x):
        s = '0' if x > 0 else '1'
        return int(s + '1' * _Exponent_bits[precision] + '0' * _Fraction_bits[precision], 2)

    # NaN
    if math.isnan(x):
        return int('0' + '1' * _Exponent_bits[precision] + '1' * _Fraction_bits[precision], 2)

    if not float_in_range(x, precision):
        raise ValueError("Value out of range for precision")

    # Get exponent and upper fraction
    l = abs(int(x))  # TODO check abs()
    f_upper = bin(l)[3:]  # remove 0b1 (includes leading 1 implied in fp)
    e = bin(len(f_upper) + _Bias[precision])[2:2 + _Exponent_bits[precision]]

    # Get lower fraction
    r = abs(x) - l  # TODO check abs()
    fraction_bits = len(f_upper)
    f_lower = ''
    while r != 0.0 and fraction_bits <= _Fraction_bits[precision]:
        r *= 2
        fraction_bits += 1
        f_lower = f_lower + str(int(r))
        r -= int(r)

    # Get sign and join
    sign = '1' if x < 0 else '0'
    res = zfill_right(sign + e + f_upper + f_lower, _Bitwidth[precision])
    return int(res, 2)


def fp_to_float(fp, precision='single'):
    """ Interpret the bitpattern of fp (an integer) as a
        floating point number, and return a Python float

    :param fp:
    :param precision:
    :return:
    """

    if precision not in ('half', 'single', 'double', 'quad'):
        raise ValueError("Precision must be one of 'half', 'single', 'double', or 'quad")
    if not isinstance(fp, int):
        raise TypeError("fp must be an integer")

    fp = bin(fp)[2:].zfill(_Bitwidth[precision])
    s = fp[0]
    e = fp[1:1 + _Exponent_bits[precision]]
    f = fp[1 + _Exponent_bits[precision]:]

    if e == '0' * _Exponent_bits[precision]:
        if f == '0' * _Fraction_bits[precision]:
            return 0.0
        else:
            raise ValueError("Subnormal number not supported")
    elif e == '1' * _Exponent_bits[precision]:
        if f == '0' * _Fraction_bits[precision]:
            return math.inf if s == '0' else -math.inf
        else:
            # Or float('nan') (Using math.nan permits object comparision, i.e. x is math.nan)
            return math.nan

    ev = 2 ** (int(e, 2) - _Bias[precision])
    fv = 1 + (int(f, 2) / 2 ** _Fraction_bits[precision])
    v = ev * fv
    return v if s == '0' else -v


def _fp_get_parts_wv(w, precision):
    if precision == 'half':
        return pyrtl.chop(w, 1, _Exponent_bits['half'], _Fraction_bits['half'])
    elif precision == 'single':
        return pyrtl.chop(w, 1, _Exponent_bits['single'], _Fraction_bits['single'])
    elif precision == 'double':
        return pyrtl.chop(w, 1, _Exponent_bits['double'], _Fraction_bits['double'])
    elif precision == 'quad':
        return pyrtl.chop(w, 1, _Exponent_bits['quad'], _Fraction_bits['quad'])
    else:
        raise ValueError("Precision must be one of 'half', 'single', 'double', or 'quad'")


def fp_add(x, y, precision='single'):
    """
    :param Wire x: a floating point number
    :param Wire y: a floating point number
    :param string precision: one of 'half', 'single', (default), 'double', or 'quad
        meaning 16, 32, or 64 bits respectively
    :return Wire: the result of floating point addition
    """
    if precision not in ('half', 'single', 'double', 'quad'):
        raise ValueError("Precision must be one of 'half', 'single', 'double', or 'quad")

    # Extract the parts
    sx, ex, fx = _fp_get_parts_wv(x, precision)
    sy, ey, fy = _fp_get_parts_wv(y, precision)

    # Exponent difference
    x_gt_y = pyrtl.signed_gt(ex, ey)
    high = pyrtl.select(x_gt_y, ex, ey)
    low = pyrtl.select(x_gt_y, ey, ex)
    sh_amt = signed_sub(high, low)

    # Shift significand of number with lesser exponent to the right
    significand_x = pyrtl.concat(pyrtl.Const(1, 1), fx)
    significand_y = pyrtl.concat(pyrtl.Const(1, 1), fy)
    with pyrtl.conditional_assignment:
        with x_gt_y:
            significand_y = pyrtl.shift_right_logical(significand_y, sh_amt)
        with pyrtl.otherwise:
            significand_x = pyrtl.shift_right_logical(significand_x, sh_amt)

    # Add significands
    with pyrtl.conditional_assignment:
        with sx:
            significand_x = negate(significand_x)
        with sy:
            significand_y = negate(significand_y)
    res = significand_x + significand_y  # TODO signed_add?

    # Normalize the sum, checking for overflow/underflow
    bits_for_normalize = count_zeroes_from_end(res)
    res = pyrtl.shift_right_logical(res, bits_for_normalize)

    # Round the sum (TODO, right now just truncating)
    sign = res[-1]
    res = res[:-1]
    res = res.truncate(_Fraction_bits[precision])

    # TODO repeat normalization and round until done
    # TODO deal with NaN/Inf/underflow/overflow

    exponent = signed_sub(pyrtl.select(x_gt_y, ey, ex),
                          bits_for_normalize).truncate(_Exponent_bits[precision])
    final = pyrtl.concat(sign, exponent, res)
    return final
