"""starfish_capture.py: a capture experiment on chapter 4f's starfish (chapters 34 and 35). Agents start in a band
within 1.5 cm of the starfish's outline, diffuse, and are carried by the IB2d flow; an agent that touches the starfish
stays there (sticky collisions, and the 'captured' state of chapter 35's CaptureSwarm). The same agents, the same
seed, in still water, for comparison.

    python starfish_capture.py path/to/Starfish_Channel [out_dir]

Writes out_dir/starfish_capture.png (the captured share against time, with and without the flow; the agents at the
end, captured ones in gold) and prints the numbers.

Licence: the CaptureSwarm class follows the pattern of Planktos's examples/ex_sticky_seafan_3d.py (W. C. Strickland,
GPL-3.0), so this file is GPL-3.0 as well; the other scripts of this folder are under the repository's LICENSE-CODE.
"""
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.path import Path
import numpy as np
import planktos
from planktos import motion

from starfish_env import load, starfish_vertex


class CaptureSwarm(planktos.Swarm):
    """Chapter 35's pattern: Euler-Maruyama drift-diffusion (fluid + noise); captured agents are held in place."""
    def apply_agent_model(self, dt):
        proposed = motion.Euler_brownian_motion(self, dt)
        held = self.get_prop("captured")[:, None]
        return np.ma.where(held, self.positions, proposed)

    def after_move(self, dt):
        hit = self.ib_collision_idx >= 0
        self.props.loc[hit, "captured"] = True


def band_start(star, n, width, rng):
    """n points outside the starfish and within width of its outline (rejection sampling in its bounding box)."""
    poly = Path(star)
    lo, hi = star.min(axis=0) - width, star.max(axis=0) + width
    pts = []
    while len(pts) < n:
        p = rng.uniform(lo, hi, size=(4 * n, 2))
        out = ~poly.contains_points(p)
        d = np.min(np.hypot(p[:, None, 0] - star[None, :, 0], p[:, None, 1] - star[None, :, 1]), axis=1)
        pts.extend(p[out & (d < width) & (d > 0.002)])          # not closer than one grid cell to start with
    return np.array(pts[:n])


def run(env, IC, dt, seed=2026, cov=2.0e-6):
    s = CaptureSwarm(envir=env, init=IC, ib_condition="sticky", seed=seed, store_prop_history=True)
    s.props["captured"] = np.zeros(s.N, dtype=bool)
    s.shared_props["cov"] = np.eye(2) * cov                     # cov = 2D: D = 1e-6 m^2/s
    share = [0.0]
    for _ in range(int(round(env.flow_times[-1] / dt))):
        s.move(dt, silent=True)
        share.append(float(s.props["captured"].mean()))
    return s, np.array(share)


RUN = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "planktos_out"
t0 = time.time()
env = load(RUN, OUT)
_, star = starfish_vertex(RUN, OUT)
rng = np.random.default_rng(7)
IC = band_start(star, 1500, 0.015, rng)
dt = 0.001
s_flow, share_flow = run(env, IC, dt)
T = np.arange(len(share_flow)) * dt
still = load(RUN, OUT)                                        # the same environment, the flow set to zero
still.flow = [np.zeros_like(c) for c in still.flow]
s_still, share_still = run(still, IC, dt)
print("%d agents within 1.5 cm of the outline, %d steps of %g s (%.0f s)" % (len(IC), len(T) - 1, dt, time.time() - t0))
for t in (0.1, 0.2, 0.38):
    k = int(round(t / dt))
    print("t = %.2f s: captured with the flow %.1f %%, in still water %.1f %%" % (t, 100 * share_flow[k], 100 * share_still[k]))
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1, 1.5]})
ax[0].plot(T, 100 * share_flow, "k", label="IB2d flow + diffusion")
ax[0].plot(T, 100 * share_still, "k--", label="still water, diffusion only")
ax[0].set_xlabel("Planktos time t (s)"); ax[0].set_ylabel("captured (% of agents)"); ax[0].legend(fontsize=8)
P = s_flow.positions; cap = s_flow.props["captured"].to_numpy()
ax[1].fill(star[:, 0], star[:, 1], color="0.85", ec="k", lw=0.8)
ax[1].plot(P[~cap, 0], P[~cap, 1], ".", ms=2, color="darkgreen", label="free")
ax[1].plot(P[cap, 0], P[cap, 1], ".", ms=3, color="gold", mec="darkgoldenrod", mew=0.3, label="captured")
ax[1].set_aspect("equal"); ax[1].set_xlim(0.22, 0.40); ax[1].set_ylim(0.06, 0.19)
ax[1].set_title("with the flow, t = %.2f s" % T[-1], fontsize=9); ax[1].legend(fontsize=8, loc="upper right")
fig.tight_layout(); fig.savefig(os.path.join(OUT, "starfish_capture.png"), dpi=150)
print("saved", os.path.join(OUT, "starfish_capture.png"))
