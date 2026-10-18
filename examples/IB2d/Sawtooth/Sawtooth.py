"""Sawtooth (pyIB2d): a sawtooth channel whose top wall is driven up and down by target points (chapter 4c of Using
IB Software). Writes sawtooth.vertex and sawtooth.target, 0-based, and prints the two numbers the update function
needs. A Python port of matIB2d/Examples/Example_Sawtooth/give_Me_Sawtooth_Geometry.m, with the grid as parameters
(the MATLAB original is 1024 x 256; on the coarser grids tried, its target stiffness made the runs fail: README).

    python3 Sawtooth.py                 # Nx = 256, Ny = 64
    python3 Sawtooth.py 1024 256        # the original resolution (6552 points)

As a port of IB2d's MATLAB file, this file is GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), like IB2d, and
not under the repository's LICENSE-CODE.
"""
import math
import sys

Nx = int(sys.argv[1]) if len(sys.argv) > 1 else 256
Ny = int(sys.argv[2]) if len(sys.argv) > 2 else Nx // 4
numTeeth = int(sys.argv[3]) if len(sys.argv) > 3 else 12      # the MATLAB example: 12 teeth in a 12 x 3 box
Lx = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0
Ly = float(sys.argv[5]) if len(sys.argv) > 5 else 3.0
ds = Lx / (2.1 * Nx)                   # point spacing: a little under dx/2 (Nick Battista's choice)
d = 0.63                               # tooth height
w = 0.63                               # tooth width
G = 0.325                              # vertical gap between the top and bottom rows of teeth
k_Target = 1e11                        # the MATLAB example's value at 1024 x 256; laptop grids fail at every value tried (README.md)
struct_name = "sawtooth"


def one_tooth(ds, d, w):
    """A vertical rise at x = 0 from 0 to d, then a diagonal down to (w, 0); point spacing ds."""
    n_up = int(math.floor(d / ds + 1e-9)) + 1
    xH = [0.0] * n_up
    yH = [i * ds for i in range(n_up)]
    diag = math.hypot(d, w)
    n_dg = int(math.floor(diag / ds + 1e-9)) + 1
    s = [-diag / 2 + i * ds for i in range(n_dg)]
    ang = math.atan(d / w)
    xD = [si * math.cos(-ang) + d / 2 for si in s]          # rotate by -ang, shift
    yD = [si * math.sin(-ang) + w / 2 for si in s]
    # the MATLAB generator nudges the last diagonal point towards its neighbour
    xD[-1] = 0.4 * xD[-2] + 0.6 * xD[-1]
    yD[-1] = 0.4 * yD[-2] + 0.6 * yD[-1]
    return xH + xD, yH + yD


def geometry(ds, d, w, G):
    xT, yT = one_tooth(ds, d, w)
    xTop, yTop, xBot, yBot = [], [], [], []
    for j in range(numTeeth):
        xTop += [x + j * w for x in xT]; yTop += [y + G / 2 for y in yT]
        xBot += [x + j * w for x in xT]; yBot += [-y - G / 2 for y in yT]
    return xTop + xBot, yTop + yBot, len(xTop)


if __name__ == "__main__":
    x, y, N_top = geometry(ds, d, w, G)
    shift = Lx / 2 - x[len(x) // 4 - 1]      # the MATLAB: xLag(end/4) (1-based) to the middle of the box
    x = [xi + shift for xi in x]
    y = [yi + Ly / 2 for yi in y]
    with open(struct_name + ".vertex", "w", newline="\n") as f:
        f.write("%d\n" % len(x))
        for xi, yi in zip(x, y):
            f.write("%1.16e %1.16e\n" % (xi, yi))
    with open(struct_name + ".target", "w", newline="\n") as f:
        f.write("%d\n" % len(x))
        for i in range(len(x)):
            f.write("%d %1.16e\n" % (i, k_Target))
    dx = Lx / Nx
    print("Info for update_Target_Point_Positions():")
    print("G = %g (vertical gap between top and bottom)" % G)
    print("N_top = %d (points on the top row; the bottom row is the rest)" % N_top)
    print("%d points, Nx x Ny = %d x %d, dx = %.5f, ds = %.5f = %.2f dx; x in [%.3f, %.3f], y in [%.3f, %.3f]"
          % (len(x), Nx, Ny, dx, ds, ds / dx, min(x), max(x), min(y), max(y)))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(10, 2.8))
        ax.plot(x[:N_top], y[:N_top], ".", ms=2, color="tab:red", label="top row (moves)")
        ax.plot(x[N_top:], y[N_top:], ".", ms=2, color="k", label="bottom row (fixed)")
        ax.set_xlim(0, Lx); ax.set_ylim(0, Ly); ax.set_aspect("equal"); ax.legend(fontsize=8, loc="upper right")
        ax.set_title("%s: %d target points, G = %g, N_top = %d" % (struct_name, len(x), G, N_top), fontsize=9)
        fig.tight_layout(); fig.savefig(struct_name + "_geometry.png", dpi=120)
    except ImportError:
        pass
