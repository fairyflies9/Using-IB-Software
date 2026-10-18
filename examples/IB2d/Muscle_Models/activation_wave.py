"""activation_wave.py: where and when IB2d's heart tube activates its muscles (chapter 4e of Using IB Software).

    python3 activation_wave.py [path/to/HeartTube.vertex]     # writes activation_wave.png

The heart tube's give_Muscle_Activation.py (pyIB2d/Examples/HeartTube_Muscle) multiplies each muscle's force by an
activation af(x, t) of its leader point's x: a square pulse of width L_AR/10 that sweeps the middle half of the tube
(25 % buffer at each end) once per period 1/freq, then starts again at the left. This script copies that function
line for line (give_Traveling_Triggering_Coefficient) and draws af over x and t without any fluid, as the example's
test_Activation_Wave.py does; with the example's .vertex file it uses the real point positions.
"""
import sys
import numpy as np
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


def give_Traveling_Triggering_Coefficient(current_time, xLag, xPt):
    """Copied from pyIB2d/Examples/HeartTube_Muscle/give_Muscle_Activation.py (IB2d, GPL-3.0)."""
    t = current_time
    freq = 10                                   # frequency of traveling wave down tube
    Ltube = xLag[len(xLag) // 2 - 1] - xLag[0]  # length of heart tube
    buff = 0.25                                 # percent-buff on each end of heart tube
    L_AR = Ltube * (1 - 2 * buff)               # length of the actual activation region of tube
    SqWidth = L_AR / 10                         # width of the square traveling activation wave
    v = (L_AR - SqWidth) * freq                 # traveling wave velocity
    t = np.fmod(t, 1 / freq)
    xL = xLag[0] + buff * Ltube + v * t
    xR = xLag[0] + buff * Ltube + SqWidth + v * t
    x = np.logical_and(xPt >= xL, xPt <= xR)
    af_Val = np.zeros(x.shape)
    af_Val[x] = 1                               # Traveling Square Wave
    return af_Val


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if args:
        xy = np.loadtxt(args[0], skiprows=1); xLag = xy[:, 0]
    else:                                       # the example's tube: two rows from x = 1 to 4 (310 points)
        top = np.linspace(1.0, 4.0, 155); xLag = np.r_[top, top]
    leaders = xLag[: len(xLag) // 2]            # muscles run from the top row (leaders) across the tube
    ts = np.linspace(0, 0.25, 501)
    af = np.array([give_Traveling_Triggering_Coefficient(t, xLag, leaders) for t in ts])
    Ltube = xLag[len(xLag) // 2 - 1] - xLag[0]; L_AR = Ltube / 2
    print("tube from x = %.3f to %.3f (L = %.3f); active region %.3f..%.3f; pulse width %.3f; speed %.3f; period %.3f"
          % (xLag[0], xLag[len(xLag) // 2 - 1], Ltube, xLag[0] + Ltube / 4, xLag[0] + 3 * Ltube / 4, L_AR / 10, (L_AR - L_AR / 10) * 10, 0.1))
    print("muscles active at any time: %d to %d (of %d top-row points; the example has 153 muscles)" % (af.sum(axis=1).min(), af.sum(axis=1).max(), len(leaders)))
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ax.pcolormesh(leaders, ts, af, shading="nearest", cmap="Reds")
    ax.set_xlabel("x of the muscle's leader point"); ax.set_ylabel("t"); ax.set_title("af(x, t): the heart tube's travelling square pulse")
    fig.tight_layout(); fig.savefig("activation_wave.png", dpi=150)
