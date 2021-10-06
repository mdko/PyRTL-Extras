import pyrtl


class _BitonicSorter:
    """ Only created this class to store the `signed` attribute
    because I don't want to pass it around to all the helpers...
    """

    def __init__(self, signed=False):
        self.signed = signed

    def comp(self, a, b):
        lt = pyrtl.signed_lt(a, b) if self.signed else a < b
        low = pyrtl.select(lt, a, b)
        high = pyrtl.select(lt, b, a)
        return low, high

    def split(self, *args):
        mid = len(args) // 2
        return args[:mid], args[mid:]

    def cleaner(self, *args):
        upper, lower = self.split(*args)
        res = [self.comp(*t) for t in zip(upper, lower)]
        new_upper = tuple(t[0] for t in res)
        new_lower = tuple(t[1] for t in res)
        return new_upper, new_lower

    def crossover(self, *args):
        upper, lower = self.split(*args)
        res = [self.comp(*t) for t in zip(upper, lower[::-1])]
        new_upper = tuple(t[0] for t in res)
        new_lower = tuple(t[1] for t in res[::-1])
        return new_upper, new_lower

    def merge_network(self, *args):
        if len(args) == 1:
            return args
        upper, lower = self.cleaner(*args)
        return self.merge_network(*upper) + self.merge_network(*lower)

    def block(self, *args):
        upper, lower = self.crossover(*args)
        if len(upper + lower) == 2:
            return upper + lower
        return self.merge_network(*upper) + self.merge_network(*lower)

    def bitonic_helper(self, *args):
        if len(args) == 1:
            return args
        else:
            upper, lower = self.split(*args)
            new_upper, new_lower = self.bitonic_helper(*upper), self.bitonic_helper(*lower)
            return self.block(*new_upper + new_lower)


def bitonic_sort(*args, signed=False):
    if len(args) == 0:
        raise pyrtl.PyrtlError("bitonic_sort requires at least one argument to sort")
    if len(args) & (len(args) - 1) != 0:
        raise pyrtl.PyrtlError("number of arguments to bitonic_sort must be a power of 2")

    bs = _BitonicSorter(signed=signed)
    return bs.bitonic_helper(*args)
