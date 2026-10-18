"""starfish_ftle.py: forward-time FTLE fields of chapter 4f's starfish flow (chapters 34 and 35), for tracers and for
swimmers: Planktos's calculate_FTLE on a grid of starting points, integrated over the 5 Hz pulse (Planktos t = 0 to
0.2 s, the run's 0.02 to 0.22 s) with the starfish as an immersed boundary and its inside masked (testdir='x1').
Tracers move with the fluid (RK45); the swimmers are a Swarm subclass whose deterministic rule adds 0.1 m/s in +x to the
fluid's velocity (Euler steps of dt; the same rule for every agent, as an FTLE map needs).

    python starfish_ftle.py path/to/Starfish_Channel [out_dir] [nx ny]

nx ny: the grid of starting points (default 256 64: about 2.5 minutes for the tracers on a desktop PC; 128 32 takes
40 s). Writes out_dir/starfish_ftle_planktos.png (Planktos's plot_2D_FTLE of the tracers), starfish_ftle.png (tracers
and swimmers side by side near the jet and the starfish) and starfish_ftle.npz, and prints ranges and times.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import planktos

from starfish_env import load, starfish_vertex


class Swimmers(planktos.Swarm):
    """The fluid's velocity plus 0.1 m/s in +x: deterministic, so the FTLE of its map means something (chapter 35)."""
    def apply_agent_model(self, dt):
        return self.positions + (self.get_fluid_drift() + np.array([0.1, 0.0])) * dt


RUN = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "planktos_out"
NX, NY = (int(sys.argv[3]), int(sys.argv[4])) if len(sys.argv) > 4 else (256, 64)
env = load(RUN, OUT)
_, star = starfish_vertex(RUN, OUT)
fields = {}
for name, kw in (("tracers", {}), ("swimmers, +0.1 m/s in x", {"swrm": Swimmers(envir=env, init=(0.5, 0.125))})):
    t0 = time.time()
    # T is the END time of the integration (it must exceed t0); dt is how often the immersed boundary is checked
    # (tracers) or the Euler step (a swarm).
    env.calculate_FTLE(grid_dim=(NX, NY), testdir="x1", t0=0, T=0.2, dt=0.002, **kw)
    F = np.ma.masked_invalid(env.FTLE_largest)
    print("%s: FTLE on %d x %d starting points, t0 = 0, T = 0.2 s: %.0f s; largest exponent %.3g to %.3g 1/s; "
          "%d points masked" % (name, NX, NY, time.time() - t0, F.min(), F.max(), np.ma.count_masked(F)))
    if name == "tracers":
        env.plot_2D_FTLE()
        plt.gcf().savefig(os.path.join(OUT, "starfish_ftle_planktos.png"), dpi=150)
        plt.close("all")
    # FTLE_loc is the starting grid as a masked array (the points inside the starfish masked): take its data.
    X = np.ma.getdata(env.FTLE_loc[:, 0]).reshape(NX, NY); Y = np.ma.getdata(env.FTLE_loc[:, 1]).reshape(NX, NY)
    fields[name] = F.reshape(NX, NY)
np.savez(os.path.join(OUT, "starfish_ftle.npz"), X=X, Y=Y, **{k.split(",")[0]: v.filled(np.nan) for k, v in fields.items()})
vmax = float(max(np.percentile(Z.compressed(), 99) for Z in fields.values()))
fig, axs = plt.subplots(2, 1, figsize=(9, 5.4), sharex=True)
for ax, (name, Z) in zip(axs, fields.items()):
    pc = ax.pcolormesh(X, Y, Z, cmap="viridis", vmin=0, vmax=vmax, shading="auto")
    ax.fill(star[:, 0], star[:, 1], color="white", ec="k", lw=0.8)
    ax.axvline(0.04, color="w", lw=0.6, ls=":"); ax.axvline(0.06, color="w", lw=0.6, ls=":")
    ax.set_aspect("equal"); ax.set_xlim(0, 0.6); ax.set_ylim(0, 0.25); ax.set_ylabel("y (m)")
    ax.set_title("largest forward FTLE (1/s), t0 = 0, T = 0.2 s: %s" % name, fontsize=9)
    fig.colorbar(pc, ax=ax, shrink=0.9)
axs[-1].set_xlabel("x (m); dotted: the forcing box")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "starfish_ftle.png"), dpi=150)
print("saved", os.path.join(OUT, "starfish_ftle.png"), "and starfish_ftle_planktos.png")
