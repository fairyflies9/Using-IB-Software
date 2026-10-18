"""starfish_vicsek.py: Vicsek alignment around chapter 4f's starfish, in still water and in the run's flow (chapters 34
and 35). Each agent swims at speed v along a heading: the direction of the mean velocity of its neighbours within r
(itself included), plus uniform noise of width nu; then it moves with its swimming velocity plus the fluid's. As in
chapter 35's capstone the neighbours' velocities are the ones move() sets from each step's displacement (swimming
plus fluid; the slide along the starfish after a hit), and distances are
wrapped only along the periodic axis (x; the channel's y boundaries are not periodic). The headings start at random,
so alignment has to emerge; the polarization |sum of swimming velocities| / (N v) measures it (1: all aligned).

    python starfish_vicsek.py path/to/Starfish_Channel [out_dir]

Demonstration values: v = 0.1 m/s, r = 2 cm, nu = 0.5 rad, dt = 2 ms, 400 agents released upstream of the starfish,
for the run's 0.38 s. Writes out_dir/starfish_vicsek.png and prints the polarization at a few times.
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


class Vicsek(planktos.Swarm):
    def __init__(self, *args, v=0.1, nu=0.5, r=0.02, **kwargs):
        super().__init__(*args, **kwargs)
        self.shared_props.update(v=v, nu=nu, r=r)
        self.theta = 2 * np.pi * self.rndState.random(self.N)          # random headings
        self.polar = []

    def apply_agent_model(self, dt):
        v, nu, r = self.get_prop("v"), self.get_prop("nu"), self.get_prop("r")
        P = np.ma.getdata(self.positions)
        D = P[:, None, :] - P[None, :, :]                              # all pairs
        for k, b in enumerate(self.envir.bndry):                      # minimum image on periodic axes only
            if b[0] == "periodic":
                L = self.envir.L[k]
                D[:, :, k] = (D[:, :, k] + L / 2) % L - L / 2
        near = np.hypot(D[:, :, 0], D[:, :, 1]) < r                    # includes the agent itself
        V = np.ma.getdata(self.velocities)                             # set by move(): swimming + fluid
        mean_v = near.astype(float) @ V                                # sums; the direction is all that matters
        self.theta = np.arctan2(mean_v[:, 1], mean_v[:, 0]) + nu * (self.rndState.random(self.N) - 0.5)
        swim = v * np.column_stack((np.cos(self.theta), np.sin(self.theta)))
        self.polar.append(np.hypot(*swim.sum(axis=0)) / (self.N * v))
        return self.positions + (swim + self.get_fluid_drift()) * dt


def run(env, IC, dt, seed):
    s = Vicsek(envir=env, init=IC, seed=seed)
    # Before the first step the velocities are the fluid's: give the agents their random swimming velocities too.
    s.velocities = s.velocities + 0.1 * np.column_stack((np.cos(s.theta), np.sin(s.theta)))
    for _ in range(int(round(env.flow_times[-1] / dt))):
        s.move(dt, silent=True)
    return s


RUN = sys.argv[1]
OUT = sys.argv[2] if len(sys.argv) > 2 else "planktos_out"
t0 = time.time()
env = load(RUN, OUT)
_, star = starfish_vertex(RUN, OUT)
rng = np.random.default_rng(11)
N = 400
IC = np.column_stack((rng.uniform(0.15, 0.25, N), rng.uniform(0.05, 0.20, N)))
dt = 0.002
s_flow = run(env, IC, dt, seed=5)
still = load(RUN, OUT)
still.flow = [np.zeros_like(c) for c in still.flow]
s_still = run(still, IC, dt, seed=5)
T = dt * np.arange(1, len(s_flow.polar) + 1)
print("%d agents, %d steps of %g s, both runs in %.0f s" % (N, len(T), dt, time.time() - t0))
for t in (0.02, 0.1, 0.2, 0.38):
    k = min(int(round(t / dt)) - 1, len(T) - 1)
    print("t = %.2f s: polarization in still water %.3f, in the flow %.3f" % (T[k], s_still.polar[k], s_flow.polar[k]))
fig = plt.figure(figsize=(11, 3.6))
ax0 = fig.add_axes([0.06, 0.15, 0.25, 0.75])
ax0.plot(T, s_still.polar, "k--", label="still water")
ax0.plot(T, s_flow.polar, "k", label="starfish flow")
ax0.set_ylim(0, 1.02); ax0.set_xlabel("Planktos time t (s)"); ax0.set_ylabel("polarization"); ax0.legend(fontsize=8)
for j, (s, name) in enumerate(((s_still, "still water"), (s_flow, "starfish flow"))):
    ax = fig.add_axes([0.37 + 0.315 * j, 0.15, 0.29, 0.75])
    P = np.ma.getdata(s.positions)
    ax.fill(star[:, 0], star[:, 1], color="0.85", ec="k", lw=0.8)
    ax.quiver(P[:, 0], P[:, 1], np.cos(s.theta), np.sin(s.theta), color="darkgreen", scale=40, width=0.004)
    ax.set_aspect("equal"); ax.set_xlim(0.05, 0.45); ax.set_ylim(0, 0.25)
    ax.set_title("%s, t = %.2f s: headings" % (name, T[-1]), fontsize=9)
    ax.set_xlabel("x (m)")
    if j:
        ax.set_yticklabels([])
fig.savefig(os.path.join(OUT, "starfish_vicsek.png"), dpi=150)
print("saved", os.path.join(OUT, "starfish_vicsek.png"))
