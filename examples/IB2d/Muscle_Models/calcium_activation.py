"""calcium_activation.py: a calcium model of muscle activation of the kind the activation tutorial describes
(Williams et al.'s model for lamprey muscle), with ILLUSTRATIVE rate constants (chapter 4e of Using IB Software).

    python3 calcium_activation.py          # writes calcium_activation.png and prints the peaks
    python3 calcium_activation.py --ib2d   # IB2d's own version (Calcium_Dynamics.m), line for line: calcium_ib2d.png

Dimensionless variables (scaled by the number of filament binding sites): Ca = free calcium, Caf = calcium bound to
the thin filaments (0 <= Caf <= 1); C = total calcium, S = SR binding sites. While the stimulus is ON the
sarcoplasmic reticulum releases calcium; while it is OFF it takes calcium back up:
    ON:  dCa/dt = (k4 Caf - k3 Ca)(1 - Caf) + k1 (C - Ca - Caf)
    OFF: dCa/dt = (k4 Caf - k3 Ca)(1 - Caf) + k2 Ca (C - S - Ca - Caf)
    dCaf/dt = -(k4 Caf - k3 Ca)(1 - Caf)
Caf is the activation that multiplies the contractile force, P = P0 lambda(l_c) alpha(v_c) Caf.

The constants below are NOT fitted values from the literature: they were chosen so that one 5 ms stimulus gives a
twitch that peaks after about 10 ms and halves in about 60 ms, to show summation and tetanus. Change them and compare.
"""
import sys
import numpy as np
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

k1, k2, k3, k4 = 300.0, 100.0, 150.0, 30.0  # 1/s, illustrative
C, S = 2.0, 6.0                            # total calcium and SR sites, per filament site, illustrative
PULSE = 0.005                              # stimulus length (s)


def rhs(Ca, Caf, on):
    bind = (k4 * Caf - k3 * Ca) * (1.0 - Caf)
    dCa = bind + (k1 * (C - Ca - Caf) if on else k2 * Ca * (C - S - Ca - Caf))
    return dCa, -bind


def run(freq, T=0.5, dt=1e-5, n_pulses=None):
    """freq = stimuli per second (0: a single stimulus at t = 0). RK4 with a fixed step."""
    n = int(round(T / dt)); t = np.arange(n + 1) * dt
    Ca = np.zeros(n + 1); Caf = np.zeros(n + 1)
    def on(tt):
        if freq == 0:
            return tt < PULSE
        k = int(tt * freq)
        if n_pulses is not None and k >= n_pulses:
            return False
        return (tt - k / freq) < PULSE
    for i in range(n):
        o = on(t[i])
        a1, b1 = rhs(Ca[i], Caf[i], o)
        a2, b2 = rhs(Ca[i] + 0.5 * dt * a1, Caf[i] + 0.5 * dt * b1, o)
        a3, b3 = rhs(Ca[i] + 0.5 * dt * a2, Caf[i] + 0.5 * dt * b2, o)
        a4, b4 = rhs(Ca[i] + dt * a3, Caf[i] + dt * b3, o)
        Ca[i + 1] = Ca[i] + dt / 6 * (a1 + 2 * a2 + 2 * a3 + a4)
        Caf[i + 1] = Caf[i] + dt / 6 * (b1 + 2 * b2 + 2 * b3 + b4)
    return t, Ca, Caf


def ib2d_calcium(Nsteps=400001, t_Final=4.0):
    """IB2d's Calcium_Dynamics(Nsteps, t_Final) (matIB2d/Examples/Example_HeartTube/*Ca*/ and
    EM_Pump_w_Calcium_and_Muscles), line for line: forward Euler with dt = t_Final/Nsteps; k1 = 9, k2 = 50, k3 = 40,
    k4 = 19.4 per second, C = S = 200; uptake k2 Ca (C - S - Ca - Caf) at every step, release k1 (C - Ca - Caf) added
    while rem(dt i, 0.5) < 0.005; unbinding k4 Caf (no factor 1 - Caf). The defaults are what the heart tubes pass
    (T = 4 s, about 4e5 steps). Returns t, Ca, Caf for MATLAB's indices 1 .. Nsteps + 1, index i at t = (i - 1) dt."""
    k1_, k2_, k3_, k4_, C_, S_ = 9.0, 50.0, 40.0, 19.4, 200.0, 200.0
    dt = t_Final / Nsteps; period, act_period = 0.5, 0.005
    Ca = [0.0] * (Nsteps + 2); Caf = [0.0] * (Nsteps + 2)    # 1-based, as in MATLAB; index 0 unused
    for i in range(2, Nsteps + 1):
        ca, caf = Ca[i], Caf[i]
        uptake = k2_ * ca * (C_ - S_ - ca - caf)
        if (dt * i) % period < act_period:
            uptake += k1_ * (C_ - ca - caf)
        Ca[i + 1] = ca + (k4_ * caf - k3_ * ca * (1 - caf) + uptake) * dt
        Caf[i + 1] = caf + (-k4_ * caf + k3_ * ca * (1 - caf)) * dt
    Ca = np.array(Ca[1:]); Caf = np.array(Caf[1:])
    return np.arange(len(Ca)) * dt, Ca, Caf


def ib2d_main():
    t, Ca, Caf = ib2d_calcium()
    print("IB2d's Calcium_Dynamics.m, T = 4 s, dt = %.4g s" % (t[1] - t[0]))
    for k in range(8):
        m = (t >= 0.5 * k) & (t < 0.5 * (k + 1)); i = np.argmax(np.where(m, Caf, -1))
        end = Caf[m][-1]
        print("stimulus %d at t = %.1f s: Caf peak %.4f at +%.1f ms, Ca peak %.3f, Caf %.4f just before the next"
              % (k + 1, 0.5 * k, Caf[i], (t[i] - 0.5 * k) * 1e3, Ca[m].max(), end))
        if k == 0:
            after = np.where(m & (t > t[i]) & (Caf < Caf[i] / 2))[0]
            print("  first twitch: Caf halves %.1f ms after the stimulus" % ((t[after[0]] if len(after) else np.nan) * 1e3))
    plt.rcParams.update({"font.size": 9, "legend.fontsize": 7.5})
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
    axs[0].plot(t, Caf, "k-", label="Caf (activation)"); axs[0].plot(t, Ca, "c--", label="Ca (free)")
    axs[0].set_xlabel("t (s)"); axs[0].set_ylim(0, 1.05); axs[0].grid(alpha=.3); axs[0].legend(loc="upper right")
    axs[0].set_title("IB2d's Calcium_Dynamics.m: a 5 ms stimulus every 0.5 s")
    m = t < 0.5
    axs[1].plot(t[m] * 1e3, Caf[m], "k-", label="Caf"); axs[1].plot(t[m] * 1e3, Ca[m], "c--", label="Ca")
    axs[1].axvspan(0, 5, color="orange", alpha=.3, label="stimulus")
    axs[1].set_xlabel("t (ms)"); axs[1].set_yscale("log"); axs[1].set_ylim(1e-3, 20); axs[1].grid(alpha=.3)
    axs[1].legend(loc="upper right"); axs[1].set_title("the first 0.5 s (log scale)")
    fig.tight_layout(); fig.savefig("calcium_ib2d.png", dpi=150)


if __name__ == "__main__" and "--ib2d" in sys.argv:
    ib2d_main()
elif __name__ == "__main__":
    plt.rcParams.update({"font.size": 9, "legend.fontsize": 7.5})
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
    t, Ca, Caf = run(0)
    axs[0].plot(t * 1e3, Caf, "k-", label="Caf (activation)"); axs[0].plot(t * 1e3, Ca, "c--", label="Ca (free)")
    axs[0].axvspan(0, PULSE * 1e3, color="orange", alpha=.3, label="stimulus")
    axs[0].set_xlim(0, 300); axs[0].set_xlabel("t (ms)"); axs[0].grid(alpha=.3); axs[0].legend(); axs[0].set_title("one stimulus: a twitch")
    i = np.argmax(Caf); half = np.where(Caf[i:] < Caf[i] / 2)[0]
    print("single twitch: Caf peak %.4f at %.1f ms, half decay at %.1f ms; free Ca peak %.4f"
          % (Caf[i], t[i] * 1e3, (t[i + half[0]] if len(half) else np.nan) * 1e3, Ca.max()))
    for f, c in ((5, "tab:blue"), (20, "tab:green"), (50, "tab:red"), (100, "tab:purple")):
        t, Ca, Caf = run(f, T=0.5)
        axs[1].plot(t * 1e3, Caf, color=c, label="%d stimuli per second" % f)
        print("%3d Hz: Caf max %.4f, mean over the last 100 ms %.4f, min over the last 100 ms %.4f"
              % (f, Caf.max(), Caf[t > 0.4].mean(), Caf[t > 0.4].min()))
    axs[1].set_xlabel("t (ms)"); axs[1].set_ylabel("Caf"); axs[1].grid(alpha=.3); axs[1].legend(); axs[1].set_title("trains: summation, then a fused (tetanic) plateau")
    fig.tight_layout(); fig.savefig("calcium_activation.png", dpi=150)
