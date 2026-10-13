"""leaf_forces.py: the drag and lift on the tethered leaf of example IB/03
against time, from the F.NNNNN files, and the displacement of its two ends
from the X.NNNNN files (chapter 11 of Using IB Software).

usage: python3 leaf_forces.py <run folder of IB/03> [output.png]

The F files hold the Lagrangian force at every point: the force the structure
exerts on the fluid. Springs and beams pull their two or three points with
forces that cancel in the sum, so the sum over the leaf is the tether force,
and minus that sum is the force the fluid exerts on the leaf: its drag (x)
and lift (y). The course normalized them as coefficients,
    C_D = -sum(F_x) / (1/2 rho U^2 L),   C_L = -sum(F_y) / (1/2 rho U^2 L),
with S = L in 2D (force per unit depth); chapter 8b's F' = F / (rho U^2 L)
is the same without the 1/2.
"""
import os
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hier_data import read_input, read_series

run = sys.argv[1] if len(sys.argv) > 1 else "."
out = sys.argv[2] if len(sys.argv) > 2 else "leaf_forces.png"

dt = read_input(os.path.join(run, "input2d"), "DT")
rho = read_input(os.path.join(run, "input2d"), "RHO")
U = read_input(os.path.join(run, "input2d"), "V")      # the flow speed the boundary conditions tend to
L = 0.1                                                 # the leaf's length (generate_mesh2d.py)

t, F = read_series(os.path.join(run, "hier_data_IB2d"), "F", dt)
t, X = read_series(os.path.join(run, "hier_data_IB2d"), "X", dt)

F_sum = np.array([f.sum(axis=0) for f in F])            # what the examples print as integral{F}
CD = -F_sum[:, 0] / (0.5 * rho * U ** 2 * L)
CL = -F_sum[:, 1] / (0.5 * rho * U ** 2 * L)
top = np.array([x[0] for x in X])                        # point 0, the top end (y = +0.05 at t = 0)
bot = np.array([x[-1] for x in X])                       # the last point, the bottom end

print("%-6s %10s %10s %10s %12s %12s" % ("t (s)", "sum F_x", "sum F_y", "C_D", "C_L", "top x (m)"))
for tt in (0.1, 0.25, 0.5, 1.0, 1.5, 2.0):
    if t[-1] >= tt - 1e-9:
        k = int(np.argmin(abs(t - tt)))
        print("%-6.2f %10.4f %10.4f %10.3f %12.3f %12.4f" % (t[k], F_sum[k, 0], F_sum[k, 1], CD[k], CL[k], top[k, 0]))
k = len(t) // 2
print("mean C_D over the second half of the run: %.3f (C_L %.3f)" % (CD[k:].mean(), CL[k:].mean()))

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.0), dpi=200)
ax1.plot(t, CD, color="#1f3f7a", lw=1.6, label="drag coefficient $C_D$")
ax1.plot(t, CL, color="#c8102e", lw=1.6, label="lift coefficient $C_L$")
ax1.plot(t, np.tanh(2 * t) ** 2 * CD[-1], color="gray", lw=0.8, ls=":", label=r"$C_D(2\,\mathrm{s})\,\tanh^2(2t)$")
ax1.set_xlabel("time (s)")
ax1.set_ylabel("force / (½ ρ U² L)")
ax1.grid(alpha=0.25)
ax1.legend(fontsize=6, frameon=False)
ax2.plot(t, 100 * (top[:, 0] - top[0, 0]), color="#1f3f7a", lw=1.6, label="top end, x")
ax2.plot(t, 100 * (bot[:, 0] - bot[0, 0]), color="#c8102e", lw=1.6, label="bottom end, x")
ax2.plot(t, 100 * (top[:, 1] - top[0, 1]), color="#1f3f7a", lw=1.0, ls="--", label="top end, y")
ax2.set_xlabel("time (s)")
ax2.set_ylabel("displacement of the ends (cm)")
ax2.grid(alpha=0.25)
ax2.legend(fontsize=6, frameon=False)
fig.tight_layout()
fig.savefig(out)
print("wrote", out)
