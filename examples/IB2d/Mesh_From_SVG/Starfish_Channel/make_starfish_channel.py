"""make_starfish_channel.py: IB2d's MeshmerizeMe starfish (matIB2d/Examples/Example_Meshmerize_Me/Flow_Around_Starfish)
as a pyIB2d example (chapter 4f of Using IB Software).

    python3 make_starfish_channel.py path/to/starfish_final.svg

Reads Lx, Ly, Nx, string_name from ./input2d, samples the starfish outline of the SVG with ../svg_to_vertex.py at
ds = Lx/(2 Nx), sizes it to 0.0803 (the largest dimension of the MATLAB example's starfish) and centres its bounding
box at (0.3125, 0.125) (the MATLAB script centres the mean of its points there: this starfish sits 0.0025 higher), adds two channel walls at y = 0.01 and y = 0.24 across the box (spacing ds;
the MATLAB example uses 2 ds), and writes <string_name>.vertex and .target (0-based indices; target stiffness 2.5e5
on the starfish and 2e7 on the walls, as in the MATLAB example). The SVG is not copied here: it is part of IB2d
(GPL-3.0), and its outline comes from a NOAA photograph (see the chapter).
"""
import os
import sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from svg_to_vertex import read_input2d, svg_to_points   # noqa: E402

K_STAR, K_WALL = 2.5e5, 2e7
SIZE, CENTER = 0.0803, (0.3125, 0.125)
Y_WALLS = (0.01, 0.24)

if __name__ == "__main__":
    svg = sys.argv[1]
    p = read_input2d(os.path.join(os.getcwd(), "input2d"))
    Lx, Ly, Nx = p["Lx"], p["Ly"], p["Nx"]
    contours, info, ds, npieces = svg_to_points(svg, Lx, Ly, Nx, fit="uniform", size=SIZE, center=CENTER)
    if len(contours) != 1:
        print("warning: %d contours in the SVG; all are used" % len(contours))
    star = np.vstack(contours)
    nw = int(round(Lx / ds))
    xw = np.arange(nw) * ds
    walls = np.vstack([np.c_[xw, np.full(nw, y)] for y in Y_WALLS])
    P = np.vstack([star, walls])
    name = p["string_name"]
    with open(name + ".vertex", "w", newline="\n") as f:
        f.write("%d\n" % len(P))
        for x, y in P:
            f.write("%1.16e %1.16e\n" % (x, y))
    with open(name + ".target", "w", newline="\n") as f:
        f.write("%d\n" % len(P))
        for i in range(len(P)):
            f.write("%d %1.16e\n" % (i, K_STAR if i < len(star) else K_WALL))
    d = np.hypot(*np.diff(np.vstack([star, star[:1]]), axis=0).T)
    print("starfish: %d points from %d path pieces, size %.4f x %.4f, centre (%.4f, %.4f); spacing/ds min %.3f median %.3f max %.3f"
          % (len(star), npieces, np.ptp(star[:, 0]), np.ptp(star[:, 1]), star[:, 0].mean(), star[:, 1].mean(), d.min() / ds, np.median(d) / ds, d.max() / ds))
    print("walls: 2 x %d points at y = %s, spacing ds = %.6g; total %d points -> %s.vertex, %s.target" % (nw, Y_WALLS, ds, len(P), name, name))
