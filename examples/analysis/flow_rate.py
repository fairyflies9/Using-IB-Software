"""flow_rate.py: the volumetric flow rate across a line, frame by frame, from IBAMR's VisIt dumps (chapter 33).

The 2020 MATLAB lecture's flappy_ends.m / vol_flow_rate.m did this with importsamrai.m: read the fluid dumps,
interpolate the velocity to a uniform grid, integrate u across the end of a tube at every saved time. The same
here with samrai_dumps.py, for any run:

    python flow_rate.py <viz dir> x=<x0> y=<y_lo>:<y_hi> [out=flux.csv] [plot=flux.png] [label=...]
        the flow rate of U[0] across the vertical line x = x0, y_lo <= y <= y_hi (per unit depth in 2D)
    python flow_rate.py <viz dir> y=<y0> x=<x_lo>:<x_hi> ...
        the flow rate of U[1] across the horizontal line y = y0
Several lines at once: x=1.0,2.0,3.0 (one column per line). Writes time and flow rate per frame, and the mean.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import samrai_dumps as sd  # noqa: E402


def fluxes(viz, lines, states=None):
    """lines: list of ('x', x0, lo, hi) or ('y', y0, lo, hi). Returns times (n,), flux (n, len(lines))."""
    frames = sd.frames(viz)
    if states is not None:
        frames = [frames[k] for k in states]
    times, out = [], []
    for step, t, folder in frames:
        d = sd.Dump(folder)
        x, y, (u, v) = d.uniform("U")
        d.close()
        row = []
        for kind, c, lo, hi in lines:
            if kind == "x":
                row.append(sd.line_flux(x, y, u, c, lo, hi))
            else:                                   # a horizontal line: swap the roles of x and y
                row.append(sd.line_flux(y, x, v.T, c, lo, hi))
        times.append(t); out.append(row)
    return np.array(times), np.array(out)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(0)
    viz = sys.argv[1]
    opt = dict(a.split("=", 1) for a in sys.argv[2:])
    lines = []
    if "x" in opt and ":" in opt.get("y", ""):
        lo, hi = (float(v) for v in opt["y"].split(":"))
        lines = [("x", float(c), lo, hi) for c in opt["x"].split(",")]
    elif "y" in opt and ":" in opt.get("x", ""):
        lo, hi = (float(v) for v in opt["x"].split(":"))
        lines = [("y", float(c), lo, hi) for c in opt["y"].split(",")]
    else:
        sys.exit("give x=<x0> y=<lo>:<hi> or y=<y0> x=<lo>:<hi>")
    states = None
    if "states" in opt:
        a, b = opt["states"].split(":"); states = range(int(a), int(b) + 1)
    t, q = fluxes(viz, lines, states)
    names = ["%s=%g" % (k, c) for k, c, _, _ in lines]
    print("time," + ",".join(names))
    for ti, row in zip(t, q):
        print("%.6g," % ti + ",".join("%.6g" % v for v in row))
    print("# mean over the frames: " + ", ".join("%s: %.6g" % (n, m) for n, m in zip(names, q.mean(axis=0))))
    if "out" in opt:
        np.savetxt(opt["out"], np.column_stack([t, q]), delimiter=",", header="time," + ",".join(names), comments="")
    if "plot" in opt:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 3.2))
        for k, n in enumerate(names):
            ax.plot(t, q[:, k], label=n)
        ax.set_xlabel("time"); ax.set_ylabel("flow rate across the line"); ax.legend(fontsize=8)
        if "label" in opt:
            ax.set_title(opt["label"], fontsize=9)
        ax.grid(alpha=0.3); fig.tight_layout(); fig.savefig(opt["plot"], dpi=150); print("# wrote", opt["plot"])
