from collections import defaultdict
from warnings import warn
import sys

import pyrtl

# TODO update to taken in the number itself (user can partially apply if they want)
# TODO use number's width as default for one of the arguments
# TODO simplify/explain arguments more
def binf(width, max_width):
    """
    Prints a number in binary with each quartet separated by a space.
    Will pad with zeros to the left up to width, and then pad with
    spaces to the left after that up to max_width.

    :param width: Size of number; will left-pad the number with
        zeroes.
    :param max_width: Number of bits (0 or 1) after the leading
        '0b' to the end of the string; doesn't include the spaces
        separating each quarter.
    :return: A function that takes a number and returns it formatted
        accordingly as a string.

    Example: binf(5, 7)(3) -> '0b  0 0011
             binf(7, 7)(9) -> '0b000 1001
    """
    def f(x):
        n = bin(x)[2:].zfill(width)
        n = ' ' * (max_width - len(n)) + n
        by_fours = [n[::-1][i:i + 4][::-1] for i in range(0, len(n), 4)][::-1]
        return '0b' + ' '.join(by_fours)
    return f

def print_memory(sim, mem, addr, count=1, format='x', size='w', file=sys.stdout):
    """ Print the values of a memory in a readable format, akin to GDB.

    :param sim: simulator instance which contains memory values.
    :param mem: the memory (or name of a memory) to examine.
    :param addr: memory address to start from. Defaults to 0.
    :param count: the number of objects to print. Defaults to 1; if a
        negative number is given, memory is examined backwards from the address.
        Setting it to None prints the entire rest of the memory.
    :param format: how to print each object.
        Options are: 'o' (octal), 'x' (hex), 'd' (decimal), 'u' (unsigned decimal),
        't' (binary), 'f' (float), 'a' (address), 'i' (instruction), 'c' (char), 's' (string)
        and 'z' (hex, zero padded on the left). Defaults to hex.
    :param size: the size of the objects.
        Options are: 'b' (byte), 'h' (halfword), 'w' (word), 'g' (giant).
        Defaults to size of the bitwidth of each element in memory, which we'll
        call your "word" size. In 32-bit memories, the word size is 4 bytes, such
        that 'h' is 2 bytes, 'g' is 8 bytes.

    If your memory uses a bitwidth of 14, 'h' corresponds to 7 bits, 'b' to 4, and 'g' to 28.
    We round down if the bitwidth/2 or bitwidth/4 is not an even number.
    Each line printed will be 4 words long.
    """

    if isinstance(mem, str):
        mem = sim.block.memblock_by_name(mem)
    addr_width = mem.addrwidth
    word_size = mem.bitwidth
    count = 2**mem.addrwidth if count is None else count

    if size =='b':
        object_size = word_size // 4
    elif size == 'h':
        object_size = word_size // 2
    elif size == 'w':
        object_size = word_size
    elif size == 'g':
        object_size = word_size * 2
    else:
        raise pyrtl.PyrtlError("Invalid word_size")

    mem = sim.inspect_mem(mem)
    mem = defaultdict(lambda: 0, mem)

    # Match format with pyrtl's val_to_formatted_str() acceptable arguments
    if format == 't':
        format = 'b'
    elif format == 'a':
        format = 'x'
    elif format == 'i':
        warn("Format 'i' not yet implemented. Using 'x'.")
        format = 'x'

    # Get prefix
    prefix = ''
    if format in ('x', 'z'):
        prefix = '0x'
    elif format == 'o':
        prefix = '0o'
    elif format == 'b':
        prefix = '0b'

    # So it looks like 's3', e.g.
    format = format + str(object_size)

    # TODO deal with negative count
    if count < 0:
        raise pyrtl.PyrtlError("Negative count not yet implemented")

    # TODO deal with unaligned start address.
    # TODO do the following programmatically
    colwidth = 8

    wc = 0
    while count != 0:
        if wc % 4 == 0:
            print(f"0x{hex(addr)[2:].zfill(addr_width // 4)}: ", end='', file=file)
        # TODO extend to match width (either with zeroes, or spaces)
        val = prefix + pyrtl.val_to_formatted_str(mem[addr], format)
        print("{v: <{w}}".format(v=val, w=colwidth), end='', file=file)

        wc += 1
        count -= 1
        addr += 1

        if wc % 4 == 0 and count != 0:
            print(file=file)
        else:
            print(' '*6, end='', file=file)

# TODO not sure how useful this is; it's only wrapping two lines, and printing the
# addresses/values in a format only I care about.
def print_touched_memory(sim, mem):
    """ Print the contents of a memory (just the address that were touched during simulation).

    Any the values of any locations not printed are 0.
    """
    mem_sorted = sorted(sim.inspect_mem(mem).items(), key=lambda t: t[0])
    print(dict([(f"{a}" f"(x{a % 32}): ", f"{hex(v)} ({v})") for a, v in mem_sorted]))