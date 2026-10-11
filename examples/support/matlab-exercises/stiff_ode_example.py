"""stiff_ode_example.py: Python version of stiff_ode_example.m.

Solves the stiff equation y'(t) = -15 y(t), y(0) = 1, with Euler's method and
compares with the exact solution y(t) = exp(-15 t).

    python3 stiff_ode_example.py DT TFINAL
    python3 stiff_ode_example.py 0.05 1    # stable, decays smoothly
    python3 stiff_ode_example.py 0.1 1     # stable, but oscillates in sign
    python3 stiff_ode_example.py 0.15 1    # unstable: grows

Each Euler step multiplies y by (1 - 15 dt), so the method is stable only for
dt <= 2/15 = 0.133, and the solution changes sign every step for dt > 1/15.
The plot is saved as stiff_ode_example.png; --show also opens a window.
"""
import math
import sys
import numpy as np
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


def solve(dt, tfinal):
    N = math.ceil(tfinal / dt) + 1   # number of time levels, the last at or after tfinal
    time = dt * np.arange(N)
    y = np.zeros(N)
    y[0] = 1.0                        # initial condition
    for i in range(1, N):             # Euler's method
        y[i] = y[i - 1] + dt * (-15 * y[i - 1])
    return time, y, np.exp(-15 * time)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dt, tfinal = float(args[0]), float(args[1])
    time, y, y_exact = solve(dt, tfinal)
    plt.plot(time, y, "-b", label="Euler's method")
    plt.plot(time, y_exact, "-r", label="Exact solution")
    plt.xlabel("time")
    plt.ylabel("y")
    plt.legend()
    plt.savefig("stiff_ode_example.png", dpi=150)
    if "--show" in sys.argv:
        plt.show()
