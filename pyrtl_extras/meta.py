import inspect
import pyrtl
from collections import namedtuple

def io_wrap(*args, **kwargs):
    """ Wrap a function by instantiating it and connecting its arguments to Input wires
    and its return values to Output wires.

    Signature::

        io_wrap(func, outputs, **kwargs)
        io_wrap(func, inputs, outputs, **kwargs)

    :param func: function of form f(input_wires) -> output_wires, to elaborate and then wrap
        the argument and return wirevectors with Input/Output WireVectors.
    :param [optional] inputs: a list of the form 'name[/size] name[/size]' where size is optional
        if the function's arguments have been annotated with a bitwidth via WV* classes.
        If 'name' is not specified, the wirevector will be given the name of the parameter itself.
        If '/size' isn't given, then the  function's argument must be annotated with a bitwidth
        via a WV* class annotation.
    :param outputs: a list of the form 'name[/size] name[/size]', where size is optional.
        If '/size' is not given, then the Output wire will be the same size as the corresponding
        return wirevector from the function to which it connects.  The 'name' portion is not optional.
    :param **kwargs: non-WireVector arguments to pass directly to the function.
    :return: a namedtuple whose fields are the Input and Output wires created, and which are accessible
        via their names.

    A ton of caveats:
    - Every optional (i.e. keyword) argument must be explicitly supplied for this to work right now.
    - It is expected that the keyword arguments are *not* wirevectors; Inputs will not be created for them.
    - For non-keyword (positional) arguments that aren't wirevectors, to avoid them accidentally being
      assumed as input wires, pass in the function partially applied with the scalar values already
      applied, so the positional arguments are only wires
    - Probably many more I'm forgetting
    """

    if len(args) == 2:
        func, input_names_sizes, output_names_sizes = args[0], None, args[1]
    elif len(args) == 3:
        func, input_names_sizes, output_names_sizes = args[0], args[1], args[2]
    else:
        raise ValueError(
            "Signature: io_wrap(func, output_names) or "
            "io_wrap(func, input_names, output_names)"
        )

    if input_names_sizes is not None and isinstance(input_names_sizes, str):
        input_names_sizes = input_names_sizes.split(' ')
    if output_names_sizes is not None and isinstance(output_names_sizes, str):
        output_names_sizes = output_names_sizes.split(' ')

    sig = inspect.signature(func)
    params = sig.parameters.copy()
    for kw_arg in kwargs.keys():
        del params[kw_arg]

    args = []
    for ix, param_name in enumerate(params):
        param = sig.parameters[param_name]
        if input_names_sizes is None:
            name, bitwidth = param.name, ''
        else:
            try:
                name, bitwidth = input_names_sizes[ix].split('/')
            except ValueError:
                name, bitwidth = input_names_sizes[ix], ''

        if bitwidth == '':
            if param.annotation is inspect.Parameter.empty:
                raise ValueError(
                    f"Parameter {param.name} must be annotated or the "
                    "bitwidth given with the parameter name, such as 'wire/8'"
                )
            bitwidth = param.annotation.bitwidth
        else:
            bitwidth = int(bitwidth)

        if name == '':
            name = param.name

        args.append(pyrtl.Input(bitwidth=bitwidth, name=name))
    res = func(*args, **kwargs)
    if not isinstance(res, tuple):
        res = (res,)
    rets = []
    for ix, (r, name) in enumerate(zip(res, output_names_sizes)):
        try:
            name, bitwidth = name.split('/')
        except ValueError:
            name, bitwidth = name, ''
        if bitwidth == '':
            bitwidth = len(r)
        else:
            bitwidth = int(bitwidth)
        o = pyrtl.Output(bitwidth=bitwidth, name=name)
        o <<= res[ix]
        rets.append(o)

    names = [a.name for a in args] + [r.name for r in rets]
    IOWrapper = namedtuple('IOWrapper', names)
    return IOWrapper(*args + rets)

class WVType:
    bitwidth = None

# This creates 128 types, named WV1, WV2, ... WV128,
# representing the bitwidths 1, 2, ..., 128 and useful for adding annotations
# to functions, like those passed to io_wrap.
g = globals()
for i in range(1, 129):
    clz_name = 'WV' + str(i)
    g[clz_name] = type(clz_name, (WVType,), {'bitwidth': i})

g['io_wrap'] = io_wrap