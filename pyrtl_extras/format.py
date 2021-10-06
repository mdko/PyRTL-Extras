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
