"""piv_to_vtk.py: a 2D vector field from two text files (one per component, as DaVis or OpenPIV export them, or as
NumPy saves them) to a legacy VTK file that VisIt opens (chapter 33; the replacement for the lab's lost toVTK.py).

    python piv_to_vtk.py Vx.txt Vy.txt out.vtk [--dx 0.5 --dy 0.5 --x0 0 --y0 0 --name U --flip]

Each text file is a rectangular array of numbers (rows = y, columns = x; whitespace- or comma-separated; lines
starting with # or letters are skipped), the same shape in both. --dx/--dy are the vector spacings (the PIV window
spacing in physical units), --x0/--y0 the position of the first column and row, --flip reverses the rows when the
first row of the file is the top of the image (DaVis) so that y increases upwards in VisIt. The output is a
STRUCTURED_POINTS dataset with one VECTORS array, which VisIt's Vector and Pseudocolor plots (magnitude(U), U[0])
and the LCS/FTLE operators take as they take an IBAMR field; the same writer serves any gridded field you compute
yourself in Python (write_vtk_vector).
"""
import argparse
import sys

import numpy as np


def read_component(path):
    rows = []
    with open(path) as f:
        for line in f:
            s = line.strip().replace(",", " ")
            if not s or s[0] in "#%" or s[0].isalpha():
                continue
            rows.append([float(v) for v in s.split()])
    return np.array(rows)


def write_vtk_vector(path, u, v, dx, dy, x0=0.0, y0=0.0, name="U", w=None):
    """u, v (and optional w) are [y, x] arrays on a uniform grid; writes a STRUCTURED_POINTS legacy VTK file."""
    ny, nx = u.shape
    if w is None:
        w = np.zeros_like(u)
    with open(path, "w", newline="\n") as f:
        f.write("# vtk DataFile Version 3.0\nPIV vector field\nASCII\nDATASET STRUCTURED_POINTS\n")
        f.write("DIMENSIONS %d %d 1\nORIGIN %g %g 0\nSPACING %g %g 1\n" % (nx, ny, x0, y0, dx, dy))
        f.write("POINT_DATA %d\nVECTORS %s double\n" % (nx * ny, name))
        for j in range(ny):                      # x fastest, then y: the VTK ordering
            for i in range(nx):
                f.write("%.9g %.9g %.9g\n" % (u[j, i], v[j, i], w[j, i]))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vx"); ap.add_argument("vy"); ap.add_argument("out")
    ap.add_argument("--dx", type=float, default=1.0); ap.add_argument("--dy", type=float, default=1.0)
    ap.add_argument("--x0", type=float, default=0.0); ap.add_argument("--y0", type=float, default=0.0)
    ap.add_argument("--name", default="U"); ap.add_argument("--flip", action="store_true")
    a = ap.parse_args()
    u, v = read_component(a.vx), read_component(a.vy)
    if u.shape != v.shape:
        sys.exit("the two files have different shapes: %s and %s" % (u.shape, v.shape))
    if a.flip:
        u, v = u[::-1], v[::-1]
    write_vtk_vector(a.out, u, v, a.dx, a.dy, a.x0, a.y0, a.name)
    print("wrote %s: %d x %d vectors, spacing %g x %g, |U| up to %g" % (a.out, u.shape[1], u.shape[0], a.dx, a.dy, np.hypot(u, v).max()))
