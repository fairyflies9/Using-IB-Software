"""starfish_kde.py: agents released just upstream of chapter 4f's starfish and carried by its IB2d flow for 0.38 s,
the run's 0.02 to 0.4 s (one 5 Hz pulse, then a rest), with a little diffusion; the end state over the vorticity, with
kernel density estimates of x and y in the margins (Planktos's own plot), and the agents' x over time with the share
of them past the starfish's centre (chapters 34 and 35).

    python starfish_kde.py path/to/Starfish_Channel [out_dir]

Writes out_dir/starfish_kde_end.png (Planktos's plot), starfish_kde_t010.png (the state at Planktos t = 0.10 s,
the run's 0.12 s, just after the forward half of the pulse, which ends at the run's 0.1 s), starfish_kde_history.png
and prints what happened.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from starfish_env import load

run = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else "planktos_out"
t_start = time.time()
env = load(run, out)
rng = np.random.default_rng(2026)                  # the initial condition's own generator (the swarm has its seed)
N = 1000
IC = np.column_stack((rng.uniform(0.18, 0.26, N), rng.uniform(0.05, 0.20, N)))
s = env.add_swarm(init=IC, seed=2026, name="tracers", color="darkgreen")
s.shared_props["cov"] = np.eye(2) * 1.0e-5          # cov = 2D: D = 5e-6 m^2/s, about 2 mm in 0.4 s
# a grid cell (1/512 m) in 2 ms at 0.96 m/s, the fastest flow where the agents go (the jet reaches 3.3 m/s)
dt = 0.001
nsteps = int(round(env.flow_times[-1] / dt))
hits = 0
for k in range(nsteps):
    s.move(dt, silent=True)
    hits += int(np.count_nonzero(s.ib_collision_idx >= 0))
print("%d agents, %d steps of %g s in %.1f s; agent-steps that touched the starfish: %d"
      % (N, nsteps, dt, time.time() - t_start, hits))
pos = s.positions
print("t = %.3f s: mean position (%.4f, %.4f); x from %.4f to %.4f; masked (left the domain): %d"
      % (env.time, pos[:, 0].mean(), pos[:, 1].mean(), pos[:, 0].min(), pos[:, 0].max(), np.ma.count_masked(pos[:, 0])))
s.plot(filename=os.path.join(out, "starfish_kde_end.png"), blocking=False, fluid="vort", dist="density",
       plot_heading=False, figsize=(10, 4.2), save_kwargs={"dpi": 150})
s.plot(t=0.1, filename=os.path.join(out, "starfish_kde_t010.png"), blocking=False, fluid="vort", dist="density",
       plot_heading=False, figsize=(10, 4.2), save_kwargs={"dpi": 150})
# The history: every stored state, mean and spread of x, and the share of agents past the starfish's centre.
H = np.ma.array(s.full_pos_history)                 # (time, agent, 2)
T = np.array(env.time_history + [env.time])
fig, ax = plt.subplots(1, 2, figsize=(10, 3.4))
ax[0].plot(T, H[:, :, 0].mean(axis=1), "k", label="mean x")
ax[0].fill_between(T, np.percentile(H[:, :, 0], 5, axis=1), np.percentile(H[:, :, 0], 95, axis=1), color="0.8",
                   label="5-95 %")
ax[0].axhspan(0.272, 0.353, color="orange", alpha=0.3, label="starfish (x)")
ax[0].set_xlabel("t (s)"); ax[0].set_ylabel("x (m)"); ax[0].legend(fontsize=8)
ax[1].plot(T, (H[:, :, 0] > 0.3125).mean(axis=1), "k")
ax[1].set_xlabel("t (s)"); ax[1].set_ylabel("share of agents with x > 0.3125 m")
fig.tight_layout(); fig.savefig(os.path.join(out, "starfish_kde_history.png"), dpi=150)
print("saved", os.path.join(out, "starfish_kde_end.png"), "and the t = 0.10 s and history pictures")
