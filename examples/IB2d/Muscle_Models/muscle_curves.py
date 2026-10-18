"""muscle_curves.py: the muscle laws of chapter 4e of Using IB Software, plotted and checked.

    python3 muscle_curves.py            # writes muscle_lt_fv.png and muscle_huxley.png, prints the checks

1. Length-tension (the Gaussian law IB2d uses):   F1(Q) = exp(-((Q - 1)/SK)^2),   Q = LF/LFO
2. Force-velocity (Hill 1938):   (P + a)(V + b) = b (P0 + a),   so   P/P0 = (b - (a/P0) V)/(V + b)
   and IB2d's normalised form F2 = (1/P0)(b P0 - a v)/(v + b) (give_Muscle_Activation.py), with a in FORCE units.
3. The combined law IB2d applies to each muscle:   Fm = af * Fmax * F1(Q) * F2(v)
4. The crossbridge model of the 2015 lecture (Huxley 1957, simplified: one attachment point, constant detachment): attach at
   x = A at rate alpha n0 (1 - U), detach at rate beta, slide at dx/dt = -v; in steady shortening
       u(x) = alpha beta/(v (alpha + beta)) exp(beta (x - A)/v)   (x <= A),   u = 0 (x > A),   U = alpha/(alpha + beta),
   and with p(x) = p1 (exp(gamma x) - 1)
       P(v) = K [(e^{gamma A} - 1) - gamma v/beta] / (1 + gamma v/beta),   K = alpha n0 p1/(alpha + beta),
   which is Hill's law with a = K, P0 = K (e^{gamma A} - 1), b = 2 N beta/gamma, V = 2 N v.
   The script integrates P = n0 * int p(x) u(x) dx numerically and compares it with the closed form.
"""
import math
import sys
import numpy as np
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


def F1(Q, SK):
    return np.exp(-((Q - 1.0) / SK) ** 2)


def hill_norm(V, a_over_P0, b):
    """Hill's law normalised: P/P0 for shortening speed V >= 0."""
    return (b - a_over_P0 * V) / (V + b)


def ib2d_F2(v, a, b, P0):
    """IB2d's F2 exactly as coded (a in force units, v = |dLF/dt|)."""
    return (1.0 / P0) * (b * P0 - a * v) / (v + b)


def huxley_closed(v, alpha, beta, gamma, A, n0p1):
    K = alpha * n0p1 / (alpha + beta)
    s = gamma * v / beta
    return K * ((math.exp(gamma * A) - 1.0) - s) / (1.0 + s)


def huxley_numeric(v, alpha, beta, gamma, A, n0p1, npts=200001):
    """P = n0 * integral_{-inf}^{A} p(x) u(x) dx with u from the steady-state solution (trapezoid rule)."""
    L = 60.0 * v / beta                       # exp(beta (x - A)/v) < e^-60 below A - L
    x = np.linspace(A - L, A, npts)
    u = alpha * beta / (v * (alpha + beta)) * np.exp(beta * (x - A) / v)
    p = np.expm1(gamma * x)                   # p(x)/p1
    return n0p1 * np.trapz(p * u, x), np.trapz(u, x)


if __name__ == "__main__":
    plt.rcParams.update({"font.size": 9, "legend.fontsize": 7.5})
    # ---------------------------------------------------------------- length-tension, force-velocity, combined
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.4))
    Q = np.linspace(0.2, 1.8, 400)
    for SK in (0.2, 0.3, 0.45):
        axs[0].plot(Q, F1(Q, SK), label="SK = %g%s" % (SK, " (the heart tube)" if SK == 0.3 else ""))
    axs[0].set_xlabel("Q = LF / LFO"); axs[0].set_ylabel("F1 (fraction of Fmax)"); axs[0].grid(alpha=.3); axs[0].legend()
    axs[0].set_title("length-tension: exp(-((Q-1)/SK)$^2$)")
    V = np.linspace(0, 20, 400)
    for aP0, b, st in ((0.25, 4.0, "b-"), (0.5, 4.0, "g-")):
        axs[1].plot(V, hill_norm(V, aP0, b), st, label="Hill, a/P0 = %g, b = %g (Vmax = %g)" % (aP0, b, b / aP0))
    axs[1].plot(V, ib2d_F2(V, 0.25, 4.0, 1e5), "r--", label="IB2d heart tube: a = 0.25, b = 4, P0 = 1e5")
    axs[1].set_xlabel("shortening speed v"); axs[1].set_ylabel("F2 (fraction of P0)"); axs[1].set_ylim(-0.05, 1.05); axs[1].grid(alpha=.3); axs[1].legend()
    axs[1].set_title("force-velocity (Hill)")
    QQ, VV = np.meshgrid(np.linspace(0.4, 1.6, 200), np.linspace(0, 16, 200))
    im = axs[2].pcolormesh(QQ, VV, F1(QQ, 0.3) * np.clip(hill_norm(VV, 0.25, 4.0), 0, None), shading="auto", cmap="viridis")
    fig.colorbar(im, ax=axs[2]); axs[2].set_xlabel("Q = LF / LFO"); axs[2].set_ylabel("v"); axs[2].set_title("F1 x F2 (SK = 0.3, a/P0 = 0.25, b = 4)")
    fig.tight_layout(); fig.savefig("muscle_lt_fv.png", dpi=150); plt.close(fig)
    v_test = np.array([0.0, 1.0, 4.0, 16.0, 1e3, 1.6e6])
    print("IB2d F2 with a = 0.25, b = 4, P0 = 1e5 at v =", v_test, ":", np.round(ib2d_F2(v_test, 0.25, 4.0, 1e5), 6))
    print("  b/(v+b) at the same v:", np.round(4.0 / (v_test + 4.0), 6), " Vmax = b P0/a =", 4.0 * 1e5 / 0.25)
    print("Hill with a/P0 = 0.25, b = 4 at the same v:", np.round(hill_norm(v_test[:4], 0.25, 4.0), 4))
    # ---------------------------------------------------------------- Huxley: check the closed form, plot u(x) and P(V)
    alpha, beta, A, n0p1, N = 1.0, 1.0, 1.0, 1.0, 1.0
    gamma = math.log(5.0) / A                 # a/P0 = 1/(e^{gamma A} - 1) = 0.25, Hill's classical value
    K = alpha * n0p1 / (alpha + beta); P0 = K * (math.exp(gamma * A) - 1)
    Vmax = 2 * N * beta / gamma * (math.exp(gamma * A) - 1)
    print("Huxley: K = a = %.4f, P0 = %.4f, a/P0 = %.4f, b = 2N beta/gamma = %.4f, Vmax = %.4f" % (K, P0, K / P0, 2 * N * beta / gamma, Vmax))
    worst = 0.0
    for v in (0.01, 0.1, 0.5, 1.0, 2.0, Vmax / (2 * N)):
        pn, Un = huxley_numeric(v, alpha, beta, gamma, A, n0p1)
        pc = huxley_closed(v, alpha, beta, gamma, A, n0p1)
        worst = max(worst, abs(pn - pc) / P0)
        print("  v = %7.4f: P numeric %.6f, closed form %.6f, U numeric %.6f (alpha/(alpha+beta) = %.6f)" % (v, pn, pc, Un, alpha / (alpha + beta)))
    print("  largest |numeric - closed| / P0 = %.2e" % worst)
    fig, axs = plt.subplots(1, 2, figsize=(9.5, 3.4))
    x = np.linspace(-3, 1.5, 800)
    for v in (0.1, 0.5, 2.0):
        u = np.where(x <= A, alpha * beta / (v * (alpha + beta)) * np.exp(beta * (x - A) / v), 0.0)
        axs[0].plot(x, u, label="v = %g" % v)
    axs[0].axvline(A, color="gray", ls=":", lw=0.8); axs[0].set_xlabel("x (crossbridge displacement)"); axs[0].set_ylabel("u(x)")
    axs[0].set_title("attached crossbridges: all attach at x = A, slide left, detach"); axs[0].grid(alpha=.3); axs[0].legend()
    vs = np.linspace(0, Vmax / (2 * N), 200); Vs = 2 * N * vs
    axs[1].plot(Vs / Vmax, [huxley_closed(v, alpha, beta, gamma, A, n0p1) / P0 for v in vs], "k-", lw=2.5, label="crossbridge model (closed form)")
    axs[1].plot(Vs / Vmax, hill_norm(Vs, K / P0, 2 * N * beta / gamma), "y--", lw=1.2, label="Hill with a = K, b = 2N beta/gamma")
    axs[1].plot([2 * N * v / Vmax for v in (0.1, 0.5, 1.0, 2.0)], [huxley_numeric(v, alpha, beta, gamma, A, n0p1)[0] / P0 for v in (0.1, 0.5, 1.0, 2.0)], "ro", ms=4, label="numerical integral")
    axs[1].set_xlabel("V / Vmax"); axs[1].set_ylabel("P / P0"); axs[1].grid(alpha=.3); axs[1].legend(); axs[1].set_title("the force-velocity curve it implies (gamma A = ln 5)")
    fig.tight_layout(); fig.savefig("muscle_huxley.png", dpi=150); plt.close(fig)
