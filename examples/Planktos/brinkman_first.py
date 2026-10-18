"""brinkman_first.py: chapter 35's first run, its slides' fragments in order, in one script (Planktos 1.0.3; all but
the add-a-swarm slide's second, explicit Swarm, which would stand still while s moves, and the properties slide's
diam and get_prop lines): an environment, Planktos's analytic Brinkman-layer flow (a porous layer under free flow),
a swarm, its properties, 24 s of drift-diffusion, the plots and the data products.

    python brinkman_first.py [out_dir]

Writes into out_dir: brinkman_flow.png (env.plot_flow), brinkman_agents.png (s.plot with velocity arrows and the
density estimates), brinkman_snapshot.png (the state stored nearest t = 8 s over the vorticity), brinkman_hist.png,
the data products of save_data, save_pos_to_csv and save_pos_to_vtk, and trial_01.mp4 when ffmpeg is on the PATH
(not run on the test machine, which has no ffmpeg; the same call with matplotlib's GIF writer in place of FFmpeg's ran).
No input data: everything is generated.
"""
import os
import shutil
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import planktos

OUT = sys.argv[1] if len(sys.argv) > 1 else "planktos_out"
os.makedirs(OUT, exist_ok=True)


def save(name):
    plt.gcf().savefig(os.path.join(OUT, name), dpi=150); plt.close("all")


# The first environment (rho and mu in the constructor: in 1.0.3 the rho and nu setters compute mu wrongly).
env = planktos.Environment(Lx=20, Ly=5, x_bndry="zero", y_bndry=["noflux", "noflux"], rho=1000, mu=1.0, units="m")
print("L", env.L, "nu", env.nu, "time", env.time)

# The Brinkman-layer flow (as Planktos's examples/basic_ex_2d.py).
env = planktos.Environment(Lx=20, Ly=5, rho=1000, mu=1000)
env.set_brinkman_flow(alpha=66, h_p=1.5, U=1, dpdx=1, res=101)
env.plot_flow(); save("brinkman_flow.png")
print("flow arrays", len(env.flow), [a.shape for a in env.flow], "flow_times", env.flow_times,
      "points", [p.shape for p in env.flow_points], "L", env.L, env.units)
print("u at the top / at the bottom of the box: %.4g / %.4g" % (env.flow[0][0, -1], env.flow[0][0, 0]))

# A swarm, its properties, and 24 s of the default motion (Euler-Maruyama: fluid + mu + noise of covariance cov*dt).
s = env.add_swarm(swarm_size=200, init="random", seed=2026, name="larvae", color="darkgreen")
print("N", s.N, "positions", s.positions.shape, "swarms", len(env.swarms))
s.shared_props["mu"] = np.array([0.0, 0.0])
s.shared_props["cov"] = np.eye(2) * (0.01 ** 2)
rng = np.random.default_rng(2026)
s.props["swim_speed"] = rng.lognormal(mean=np.log(0.02), sigma=0.15, size=s.N)
dt = 0.1
for _ in range(round(24.0 / dt)):
    s.move(dt, silent=True)
mask = np.ma.getmaskarray(s.positions)
active = ~np.all(mask, axis=1)
print("time %.1f; %d stored times; %d agents still in the domain of %d; mean velocity %s"
      % (env.time, len(env.time_history), active.sum(), s.N, np.round(s.velocities.mean(axis=0), 4)))

# Plots: the current state, the stored state nearest t = 8, a histogram.
s.plot(fluid="quiver", dist="density", circ_rad=0.08, plot_heading=False, blocking=False,
       filename=os.path.join(OUT, "brinkman_agents.png"))
s.plot(t=8.0, filename=os.path.join(OUT, "brinkman_snapshot.png"), fluid="vort", blocking=False,
       save_kwargs={"dpi": 200})
s.plot(dist="hist", blocking=False, filename=os.path.join(OUT, "brinkman_hist.png"))

# Data products, and a movie when ffmpeg is there.
s.save_data(OUT, "trial_01")
s.save_pos_to_csv(os.path.join(OUT, "trial_01_positions.csv"))
s.save_pos_to_vtk(OUT, "trial_01")
if shutil.which("ffmpeg"):
    frames = range(0, len(s.full_pos_history), 5)
    # fluid="quiver": in Planktos 1.0.3 plot_all(fluid="vort") stops on a static flow such as this one
    #   ("ValueError: not enough values to unpack (expected 2, got 1)", planktos/_swarm.py line 2548)
    s.plot_all(movie_filename=os.path.join(OUT, "trial_01.mp4"), frames=frames, fps=10, fluid="quiver",
               plot_heading=False)
else:
    print("no ffmpeg on the PATH: no movie (everything else works without it)")
print("files:", sorted(os.listdir(OUT)))
