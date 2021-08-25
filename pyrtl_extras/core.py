import pyrtl


def gray_code(n):
    """ Get the binary-reflected gray code of n """
    n = pyrtl.as_wires(n)
    return n ^ n[1:]
