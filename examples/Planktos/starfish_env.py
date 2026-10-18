"""starfish_env.py: chapter 4f's IB2d starfish channel as a Planktos 1.0.3 Environment (chapters 34 and 35).

    from starfish_env import load
    env = load("path/to/Starfish_Channel")     # the run folder: input2d, starfish_channel.vertex, viz_IB2d/

The flow: the u.####.vtk files in viz_IB2d from dump 1 on (20 dumps 0.02 s apart; dt and print_dump are read from
input2d). Dump 0 (t = 0, the fluid at rest) is skipped: pyIB2d writes that dump's velocity files (u, uX) with their
grid transposed (DIMENSIONS 128 512 for 512 x 128; IBM_Driver.py passes U, V there and U.T, V.T for every later dump;
IB2d's open issue #12 reports it for the MATLAB version), and Planktos cannot stack it with the others ("all the input
array dimensions ... must match"). Planktos starts its clock at the
first dump it reads, so the run's time is Planktos's t + 0.02 s. It shifts the data so that its first grid point
is the origin and adds the periodic end points (IB2d is periodic).
The structure: the starfish only, the points of starfish_channel.vertex with 0.02 < y < 0.23 (its first 405), joined
in order ('adjacent') and closed by one more segment, last point to first. Two Planktos 1.0.3 details: for a single
.vertex file 'adjacent' ignores periodic=True (only the moving-mesh branch reads it), so the closing segment goes in
add_idx_list; and add_idx_list is used as 0-based indices although its docstring says MATLAB's 1-based ones.
'proximity' would not do either: it joins points closer than 0.501 grid cells, and these are 0.503 apart (1.006 ds,
ds = half a cell; printed below). The two channel walls (y = 0.01 and
0.24) run across the whole box and so cross its periodic x boundary, which Planktos does not handle; noflux outer
boundaries at y = 0 and 0.25 stand in for them (the fluid between a wall and the box edge moves more slowly: a mean
speed of 0.02-0.06 m/s there against 0.04-0.44 m/s in the channel, dumps 1-20, with local speeds up to 0.56 m/s).
rho and mu go to the constructor (input2d's values): in 1.0.3 the rho and nu setters compute mu wrongly (chapter 35).
"""
import os
import re

import numpy as np
import planktos


def read_input2d(run):
    """The numbers of input2d as a dict (key = value lines, % comments)."""
    out = {}
    with open(os.path.join(run, "input2d")) as f:
        for line in f:
            m = re.match(r"\s*(\w+)\s*=\s*([-+0-9.eE]+)", line.split("%")[0])
            if m:
                out[m.group(1)] = float(m.group(2))
    return out


def starfish_vertex(run, out_dir):
    """Write the starfish's own points (no walls) as a .vertex file in out_dir; return its path and the points."""
    with open(os.path.join(run, "starfish_channel.vertex")) as f:
        n = int(f.readline())
        P = np.loadtxt(f, max_rows=n)
    star = P[(P[:, 1] > 0.02) & (P[:, 1] < 0.23)]
    path = os.path.join(out_dir, "starfish_only.vertex")
    os.makedirs(out_dir, exist_ok=True)
    with open(path, "w", newline="\n") as f:
        f.write("%d\n" % len(star))
        for x, y in star:
            f.write("%1.16e %1.16e\n" % (x, y))
    return path, star


def load(run, out_dir="planktos_out", mesh=True, d_start=1, d_finish=None):
    """The Environment: the starfish run's flow and (if mesh) the starfish as an immersed mesh."""
    p = read_input2d(run)
    env = planktos.Environment(x_bndry="periodic", y_bndry="noflux", rho=p["rho"], mu=p["mu"], units="m")
    env.read_IB2d_fluid_data(os.path.join(run, "viz_IB2d"), dt=p["dt"], print_dump=int(p["print_dump"]),
                             d_start=d_start, d_finish=d_finish)
    dx = p["Lx"] / p["Nx"]
    print("flow: %d dumps from dump %d, Planktos t = %g to %g s (run time - %g s); grid %s; L = %s; data origin "
          "(fluid_domain_LLC) = %s" % (len(env.flow_times), d_start, env.flow_times[0], env.flow_times[-1],
                                       d_start * p["print_dump"] * p["dt"], env.flow[0].shape[1:],
             [round(v, 6) for v in env.L], tuple(round(v, 6) for v in env.fluid_domain_LLC)))
    if mesh:
        path, star = starfish_vertex(run, out_dir)
        d = np.hypot(*np.diff(np.vstack([star, star[:1]]), axis=0).T)
        print("starfish: %d points, neighbours %.4f-%.4f grid cells apart (proximity joins below %.3f)"
              % (len(star), d.min() / dx, d.max() / dx, 0.501))
        env.read_IB2d_mesh_data(path, method="adjacent", add_idx_list=[(len(star) - 1, 0)])   # 0-based: closes it
        m = env.ibmesh.reshape(-1, 2)
        print("mesh: %d segments; x %.4f-%.4f, y %.4f-%.4f (the points' x %.4f-%.4f, y %.4f-%.4f)"
              % (len(env.ibmesh), m[:, 0].min(), m[:, 0].max(), m[:, 1].min(), m[:, 1].max(),
                 star[:, 0].min(), star[:, 0].max(), star[:, 1].min(), star[:, 1].max()))
    return env
