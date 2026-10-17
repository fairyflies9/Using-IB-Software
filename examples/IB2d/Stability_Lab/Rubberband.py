"""Rubberband.py: the rubber band of IB2d's Rubberband_with_Springs example, with the grid and the stiffness as
parameters (chapter 4d of Using IB Software, the stability and convergence lab).

    python3 Rubberband.py [Nx [k_Spring [ds_Rest [ppc]]]]

writes rubberband.vertex and rubberband.spring (pyIB2d's 0-based indices) for N = ppc * Nx points on the ellipse
centred at (0.5, 0.5) in the unit box with semi-axis 0.2 along x and 0.4 along y (the example's geometry function
takes (N, rmin, rmax) but is called with (N, a, b) = (N, 0.4, 0.2), so the shipped band is tall, not wide), each point joined to the next by a spring of stiffness
k_Spring and resting length ds_Rest, the last joined to the first. Defaults: Nx = 32, k_Spring = 2.5e4, ds_Rest = 0, ppc = 2:
the shipped example's files, identical to 1e-16. The shipped choice N = 2 Nx is called "2x resolution of the Eulerian
grid" in the example, but the band's perimeter is 1.94, so ds = 0.97 dx: ONE point per cell, and the band leaks (chapter
4d measures it). ppc = 4 gives ds = 0.48 dx, the two points per cell of the rules of thumb. It prints N, ds, dx and ds/dx, and saves rubberband_geometry.png
(--show opens the plot instead).

With a resting length of zero the force in each spring is k_Spring * ds, and IB2d spreads every point's force times
ITS OWN ds = Lx/(2 Nx) (IBM_Driver.py line 259: two points per cell assumed, whatever this file's spacing), so what the
fluid feels per link is k_Spring * ds_file * dx/2. Refining the grid with the same k_Spring therefore makes a band four
times softer per doubling (scale k_Spring with Nx^2 to keep it), and doubling the points on the same grid halves the
tension (scale k_Spring with the number of points). sweep.py does both; chapter 4d measures what the other choices do.
"""
import math
import sys

Lx = Ly = 1.0
A, B = 0.4, 0.2        # the example's a and b; a ends up as the y semi-axis (see the docstring)


def band(Nx, ppc=2):
    N = int(round(ppc * Nx))   # the shipped example: N = 2 Nx (one point per cell for this band, see above)
    x = [0.5 + B * math.cos(2 * math.pi * i / N) for i in range(N)]   # semi-axis 0.2 along x
    y = [0.5 + A * math.sin(2 * math.pi * i / N) for i in range(N)]   # semi-axis 0.4 along y: the band is tall
    return x, y


def write_band(Nx=32, k_Spring=2.5e4, ds_Rest=0.0, name="rubberband", outdir=".", ppc=2):
    import os
    x, y = band(Nx, ppc)
    N = len(x)
    with open(os.path.join(outdir, name + ".vertex"), "w", newline="\n") as f:
        f.write("%d\n" % N)
        for xi, yi in zip(x, y):
            f.write("%1.16e %1.16e\n" % (xi, yi))
    with open(os.path.join(outdir, name + ".spring"), "w", newline="\n") as f:
        f.write("%d\n" % N)
        for s in range(N):
            f.write("%d %d %1.16e %1.16e\n" % (s, (s + 1) % N, k_Spring, ds_Rest))
    per = sum(math.hypot(x[(i + 1) % N] - x[i], y[(i + 1) % N] - y[i]) for i in range(N))
    return N, per / N, Lx / Nx


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    Nx = int(args[0]) if len(args) > 0 else 32
    k = float(args[1]) if len(args) > 1 else 2.5e4
    L = float(args[2]) if len(args) > 2 else 0.0
    ppc = float(args[3]) if len(args) > 3 else 2
    N, ds, dx = write_band(Nx, k, L, ppc=ppc)
    print("N = %d points, ds = %.5f (mean), dx = %.5f, ds/dx = %.3f, k_Spring = %g, tension k*ds = %.1f"
          % (N, ds, dx, ds / dx, k, k * ds))
    try:
        import matplotlib
        if "--show" not in sys.argv:
            matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x, y = band(Nx, ppc)
        plt.plot(x + x[:1], y + y[:1], "r-", x, y, "k*", ms=3)
        plt.xlabel("x"); plt.ylabel("y"); plt.axis("square"); plt.xlim(0, 1); plt.ylim(0, 1)
        plt.title("rubber band, %d points on a %d x %d grid" % (N, Nx, Nx))
        if "--show" in sys.argv:
            plt.show()
        else:
            plt.savefig("rubberband_geometry.png", dpi=120)
    except ImportError:
        pass
