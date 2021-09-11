import subprocess
import os
import tempfile
from inspect import signature
import itertools 
import pyrtl

def equivalent_comb_via_sim(f1, f2, bitwidths, **kwargs):
    """ Brute-force test two functions for equivalence by generating all possible values
        for each input and comparing the resulting output of each function. Requires
        that both functions have the same number and order of inputs and outputs.

        Some caveats: you should only supply non-wire arguments (i.e. what you
        would call "parameters" in Verilog) in the kwargs map. It is assumed
        that all wire arguments come before any of the arguments in kwargs,
        and these wire arguments will be generated internally here for you.

        :param f1: The first function to test
        :parma f2: The second function to test
        :param bitwidths: A list of bitwidths for each input to the functions
        :param kwargs: A map of keyword arguments to pass to the functions
    """

    sig1 = signature(f1)
    sig2 = signature(f2)
    if len(sig1.parameters) != len(sig2.parameters):
        raise pyrtl.PyrtlError("Both functions should take the same number of parameters.")
    if len(bitwidths) != len(sig1.parameters):
        raise pyrtl.PyrtlError("Must supply a bitwidth for each parameter.")

    arg_wires = [pyrtl.Input(bitwidth=bw, name='arg%d' % i) for i, bw in enumerate(bitwidths)]

    out1 = f1(*arg_wires, **kwargs)
    out2 = f2(*arg_wires, **kwargs)
    if not isinstance(out1, tuple):
        out1 = (out1,)
    if not isinstance(out2, tuple):
        out2 = (out2,)
    
    assert len(out1) == len(out2), "Both functions should return the same number of values."

    for n, o in enumerate(out1):
        pyrtl.probe(o, f"f1_out{n}")
    
    for n, o in enumerate(out2):
        pyrtl.probe(o, f"f2_out{n}")

    tracer = pyrtl.SimulationTrace()
    sim = pyrtl.Simulation(tracer)
    # Example:
    # A: 4 bits = [0b0000, 0b0001, ..., 0b1111]
    # B: 2 bits = [0b00, 0b01, 0b10, 0b11]
    # C: 3 bits = [0b000, 0b001, ..., 0b111]
    # combs = [(a, b, c) for a in A for b in B for c in C]
    # combs = [(0, 0, 0), (0, 0, 1), (0, 0, 2), ..., (0, 0, 7), (0, 1, 0), ...]
    combs = list(itertools.product(*[range(0, p.bitmask + 1) for p in arg_wires]))
    for stepn, input in enumerate(combs):
        sim.step({
            p.name: input[j] for j, p in enumerate(arg_wires)
        })
        for o1, o2 in zip(out1, out2):
            v1 = sim.inspect(o1)
            v2 = sim.inspect(o2)
            if v1 != v2:
                print(f"{v1} != {v2} for input {input} (step #{stepn})")
    
    #sim.tracer.render_trace()

def equivalent_seq_via_simulation(f1, f2, bitwidths, nsteps=None, **kwargs):
    pass

def equivalent_seq_via_cosa(f1, f2, bitwidths, **kwargs):
    """ Check if two sequential circuits are equivalent by checking in CoSA """

    def to_verilog(f):
        def instantiate():
            if isinstance(f, pyrtl.Block):
                return f
            elif callable(f):
                b = pyrtl.Block()
                with pyrtl.set_working_block(b):
                    arg_wires = [pyrtl.Input(bitwidth=bw, name='in%d' % i) for i, bw in enumerate(bitwidths)]
                    out = f(*arg_wires, **kwargs)
                    if not isinstance(out, tuple):
                        out = (out,)
                    for n, o in enumerate(out):
                        pyrtl.probe(o, f"out{n}")
                return b
            else:
                raise pyrtl.PyrtlError("Expected a block or function to instantiate, got %s" % str(type(f)))

        b = instantiate()
        tmp_vd, tmp_verilog_path = tempfile.mkstemp(prefix='pyrtl_verilog', suffix='.v', text=True)
        with open(tmp_verilog_path, "w") as f:
            pyrtl.output_to_verilog(f, block=b)

        return tmp_vd, tmp_verilog_path
        
    vfd1, vf1 = to_verilog(f1)
    vfd2, vf2 = to_verilog(f2)

    try:
        res = subprocess.run([
            "CoSA", "-i", vf1 + "[toplevel]",
            "--equal-to", vf2 + "[toplevel]",
            "--abstract-clock",
            "--zero-init",
    #        "--init outputs/tmp.init",
            "--verification", "equivalence", "--prove", "-k", "10",
        ]) #, capture_output=True, text=True)
    except:
        os.close(vfd1)
        os.close(vfd2)
    # assert ("Result: TRUE" in res.stdout.splitlines())
