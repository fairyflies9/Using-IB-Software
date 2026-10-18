"""Moving_Rubberband (pyIB2d): writes rubberband.vertex and rubberband.target for a circle of 64 target points that
update_Target_Point_Positions.py drags along a zig-zag (chapter 4c of Using IB Software).

A Python port of matIB2d/Examples/Example_Moving_Rubberband/Rubberband.m. Indices count from 0 (the Python port of
IB2d indexes its structure files that way; the MATLAB files count from 1).

    python3 Rubberband.py          # writes the two files and rubberband_geometry.png

As a port of IB2d's MATLAB file, this file is GPL-3.0 (https://www.gnu.org/licenses/gpl-3.0.html), like IB2d, and
not under the repository's LICENSE-CODE.
"""
import math

Nx = 32          # grid points in x (the generator only uses them to choose N)
Ny = 32
Lx = 1.0         # domain, the box [0, Lx] x [0, Ly]
Ly = 1.0
N = 2 * Nx       # Lagrangian points: twice the grid resolution
a = 0.2          # semi-major axis
b = 0.2          # semi-minor axis (a circle)
xc, yc = 0.25, 0.25   # centre: the band starts in the lower-left quarter and is dragged right and up
k_Target = 1e7   # target-point stiffness
struct_name = "rubberband"


def geometry(N, rmin, rmax):
    """N points on the ellipse with semi-axes rmax (x) and rmin (y), counter-clockwise from the rightmost point."""
    x = [xc + rmax * math.cos(2 * math.pi / N * i) for i in range(N)]
    y = [yc + rmin * math.sin(2 * math.pi / N * i) for i in range(N)]
    return x, y


def write_vertices(x, y, name):
    with open(name + ".vertex", "w", newline="\n") as f:
        f.write("%d\n" % len(x))
        for xi, yi in zip(x, y):
            f.write("%1.16e %1.16e\n" % (xi, yi))


def write_targets(n, k, name):
    with open(name + ".target", "w", newline="\n") as f:
        f.write("%d\n" % n)
        for i in range(n):                 # 0-based indices for pyIB2d
            f.write("%d %1.16e\n" % (i, k))


if __name__ == "__main__":
    x, y = geometry(N, a, b)
    write_vertices(x, y, struct_name)
    write_targets(N, k_Target, struct_name)
    dx = Lx / Nx
    ds = math.hypot(x[1] - x[0], y[1] - y[0])
    print("%d points, dx = %.4f, ds = %.4f = %.2f dx; wrote %s.vertex and %s.target" % (N, dx, ds, ds / dx, struct_name, struct_name))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.plot(x + x[:1], y + y[:1], "r-"); ax.plot(x, y, "k.", ms=4)
        ax.set_xlim(0, Lx); ax.set_ylim(0, Ly); ax.set_aspect("equal"); ax.set_title("%s: %d target points" % (struct_name, N))
        fig.savefig(struct_name + "_geometry.png", dpi=120)
    except ImportError:
        pass
