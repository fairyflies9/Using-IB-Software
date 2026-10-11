"""heat_equation.py: Python version of heat_equation.m, an explicit
finite-difference solution of the heat equation.

Solves u_t = u_xx for 0 < x < 1 with u(0,t) = u(1,t) = 0 and
u(x,0) = sin(2 pi x) up to t = 0.1, and compares with the exact solution
u = exp(-4 pi^2 t) sin(2 pi x).

    python3 heat_equation.py N T          # N interior points, T time steps
    python3 heat_equation.py 19 100       # dx = 0.05, dt = 0.001, r = 0.4
    python3 heat_equation.py 19 50        # r = 0.8: unstable, the solution blows up

The scheme is stable only when r = dt/dx^2 <= 1/2. Just above 1/2 (for
example 19 70, r = 0.57) the growth starts from rounding error and is still
too small to see after 70 steps. The plot is saved as
heat_equation.png (the MATLAB version wrote Example4_1.eps); --show also
opens a window.
"""
import sys
import numpy as np
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


def solve(n, T, t=0.1):
    dt = t / T
    dx = 1 / (n + 1)
    r = dt / (dx * dx)
    x = dx * np.arange(1, n + 1)     # all the inner points
    up = np.sin(2 * np.pi * x)       # initial condition
    for _ in range(T):
        un = np.empty_like(up)
        un[1:-1] = r * up[:-2] + (1 - 2 * r) * up[1:-1] + r * up[2:]
        un[0] = (1 - 2 * r) * up[0] + r * up[1]          # u(0,t) = 0
        un[-1] = r * up[-2] + (1 - 2 * r) * up[-1]       # u(1,t) = 0
        up = un
    return x, up, dx, dt, r


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    n, T = int(args[0]), int(args[1])
    x, up, dx, dt, r = solve(n, T)

    t = 0.1
    ex = np.linspace(0, 1, 201)      # 0:0.005:1
    u_ex = np.exp(-4 * np.pi**2 * t) * np.sin(2 * np.pi * ex)
    xx = np.concatenate(([0], x, [1]))
    uu = np.concatenate(([0], up, [0]))
    plt.plot(ex, u_ex, linewidth=1.2, label="exact")
    plt.plot(xx, uu, "--o", linewidth=1.2, label="numerical")
    plt.text(0.01, -0.017, "dx=%6.3g, dt=%g, r=%g" % (dx, dt, r), fontsize=14)
    plt.xlabel("x")
    plt.legend()
    plt.savefig("heat_equation.png", dpi=150)
    print("max error at t = 0.1:", np.max(np.abs(up - np.exp(-4 * np.pi**2 * t) * np.sin(2 * np.pi * x))))
    if "--show" in sys.argv:
        plt.show()
