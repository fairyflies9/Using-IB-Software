"""ibamr_plate.py: agents carried past the plate of IBFE/10's 3D flow tank (chapters 22, 33, 35): an IBAMR run, through
VisIt's resampling (examples/analysis/resample_export.py) and examples/analysis/vtk_for_planktos.py, into Planktos 1.0.3.

    python ibamr_plate.py <IBAMR_db_000.vtk, or a folder of IBAMR_db_###.vtk> [out_dir]

The flow: one file is read as a steady flow (Planktos holds it for all time); a folder as a time series. This
example uses the run's last dump (t = 0.5 s) as a steady flow: the stream was still speeding up then (U tanh 2t is 76 %
of U at t = 0.5), so a longer run would give a better one. The plate: its reference shape, a box 0 < x < 0.125,
-1 < y < 1, -1 < z < 1, written here as an STL file (numpy-stl) in the run's coordinates; Planktos shifts it with the
flow (fluid_domain_LLC). By t = 0.5 the flaps had bent 0.012 at their edges (chapter 22), a tenth of the grid spacing.
The agents: a 30 x 30 sheet 2 upstream of the plate (x = -2, -1.5 < y, z < 1.5), tracers with a little diffusion,
sliding along the plate when they hit it, moved for 60 s. Writes out_dir/ibamr_plate.png (top and side views, the
plate in grey, the agents coloured by their starting height) and Planktos's own 3D plot, ibamr_plate_planktos.png.
"""
import glob
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import planktos
from stl import mesh as stlmesh

SRC = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "planktos_out"
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
env = planktos.Environment(rho=1.0, mu=0.01)                  # IBFE/10's fluid (rho, mu in the constructor)
env.read_IBAMR3d_vtk_data(SRC)
LLC = np.array(env.fluid_domain_LLC)
print("read %s in %.1f s: L = %s, data corner (fluid_domain_LLC) = %s, flow_times = %s, max |u| = %.4g"
      % (SRC, time.time() - t0, np.round(env.L, 4), LLC, None if env.flow_times is None else len(env.flow_times),
         np.max(np.sqrt(sum(c ** 2 for c in env.flow)))))


def box_stl(lo, hi, path):
    """A closed box as 12 triangles (outward normals), saved as an STL file."""
    x0, y0, z0 = lo; x1, y1, z1 = hi
    V = np.array([[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
                  [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]])
    F = [[0, 3, 2], [0, 2, 1], [4, 5, 6], [4, 6, 7], [0, 1, 5], [0, 5, 4],
         [2, 3, 7], [2, 7, 6], [1, 2, 6], [1, 6, 5], [0, 4, 7], [0, 7, 3]]
    m = stlmesh.Mesh(np.zeros(len(F), dtype=stlmesh.Mesh.dtype))
    for i, f in enumerate(F):
        m.vectors[i] = V[f]
    m.save(path)


stl_path = os.path.join(OUT, "plate_reference.stl")
box_stl((0.0, -1.0, -1.0), (0.125, 1.0, 1.0), stl_path)
env.read_stl_mesh_data(stl_path)
print("plate mesh: %d triangles, x %.3f-%.3f in Planktos's coordinates (the run's 0-0.125 minus the corner)"
      % (len(env.ibmesh), env.ibmesh[:, :, 0].min(), env.ibmesh[:, :, 0].max()))
g = np.linspace(-1.5, 1.5, 30)
Y0, Z0 = np.meshgrid(g, g, indexing="ij")
IC = np.column_stack((np.full(Y0.size, -2.0), Y0.ravel(), Z0.ravel())) - LLC     # run coordinates -> Planktos's
s = planktos.Swarm(envir=env, init=IC, seed=35)
s.shared_props["cov"] = np.eye(3) * 1.0e-5                     # cov = 2D: D = 5e-6 (a little diffusion)
dt, T = 0.1, 60.0
hits = 0
t1 = time.time()
for _ in range(int(round(T / dt))):
    s.move(dt, silent=True)
    hits += int(np.count_nonzero(s.ib_collision_idx >= 0))
P = np.ma.getdata(s.positions) + LLC                           # back to the run's coordinates
gone = np.ma.getmaskarray(s.positions)[:, 0]
print("%d agents, %d steps of %g s in %.0f s; agent-steps that touched the plate: %d; left the box: %d"
      % (s.N, int(round(T / dt)), dt, time.time() - t1, hits, gone.sum()))
x = P[~gone, 0]
print("after %g s: x from %.2f to %.2f (mean %.2f); y spread %.2f (it started at 3.0)"
      % (T, x.min(), x.max(), x.mean(), np.ptp(P[~gone, 1])))
s.plot(filename=os.path.join(OUT, "ibamr_plate_planktos.png"), blocking=False)
c = Z0.ravel()                                                 # colour: starting height z
fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for a, (j, name) in zip(ax, ((1, "y"), (2, "z"))):
    a.add_patch(plt.Rectangle((0, -1), 0.125, 2, color="0.6"))
    a.scatter(IC[:, 0] + LLC[0], IC[:, j] + LLC[j], s=2, c="0.8")
    a.scatter(P[~gone, 0], P[~gone, j], s=4, c=c[~gone], cmap="viridis")
    a.set_xlabel("x"); a.set_ylabel(name); a.set_aspect("equal"); a.set_xlim(-3, 4); a.set_ylim(-2.5, 2.5)
    a.set_title("%s view: start (grey) and t = %g s" % ("top" if j == 1 else "side", T), fontsize=9)
fig.tight_layout(); fig.savefig(os.path.join(OUT, "ibamr_plate.png"), dpi=150)
print("saved", os.path.join(OUT, "ibamr_plate.png"), "and ibamr_plate_planktos.png")
