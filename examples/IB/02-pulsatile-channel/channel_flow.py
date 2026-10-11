"""channel_flow.py: builds the channel geometry for example IB/02 and writes
channel.vertex, channel.target, channel.spring and channel.beam.

Python version of Channel_Flow.m (Nick Battista, 2013); it writes the same
files. Run it from this folder:

    python3 channel_flow.py          # write the four files
    python3 channel_flow.py --plot   # also plot the points (needs matplotlib)

The channel is two rows of Lagrangian points, the walls y = d/2 and y = -d/2,
spanning the domain [-L/2, L/2]. The target points hold the walls in place;
the springs and beams are made so weak that they do nothing. L and d must
match the values in input2d.
"""
import sys

L = 5.0               # length of computational domain: [-L/2, L/2]
ds = L / (2 * 512)    # distance between Lagrangian points
d = 1.0               # channel diameter

# Spring, beam and target point coefficients
kappa_target = 1e4
kappa_spring = 1e-10
kappa_beam = 1e-10


def get_vertices(L, d, ds):
    """Points of the top wall, then the same x values on the bottom wall."""
    x = -L / 2 + ds / 2          # first Lagrangian point is half a step from the domain boundary
    X_top = []
    while x < L / 2:
        X_top.append(x)
        x = x + ds
    n_top = len(X_top)
    X = X_top + X_top
    Y = [d / 2] * n_top + [-d / 2] * n_top
    return X, Y, n_top


def write_vertices(X, Y):
    with open("channel.vertex", "w", newline="\n") as f:
        f.write(f"{len(X)}\n")
        for x, y in zip(X, Y):
            f.write("%1.16e %1.16e\n" % (x, y))


def write_target(X, kappa_target, ds):
    with open("channel.target", "w", newline="\n") as f:
        f.write(f"{len(X)}\n")
        for s in range(len(X)):
            f.write("%d %1.16e\n" % (s, kappa_target * ds / (ds ** 2)))


def write_spring(X, kappa_spring, ds, n_top):
    """Springs join neighbors along each wall, but not the end of the top wall
    to the start of the bottom wall."""
    N = len(X)
    spring_force = kappa_spring * ds / (ds ** 2)
    with open("channel.spring", "w", newline="\n") as f:
        f.write(f"{N - 2}\n")
        for s in range(N - 1):
            if s <= n_top - 2 or s >= n_top:
                f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, spring_force, ds))


def write_beam(X, Y, kappa_beam, ds, n_top):
    """Beams join three neighbors along each wall. The last two numbers are the
    resting curvature, which is zero for a straight wall."""
    N = len(X)
    beam_force = kappa_beam * ds / (ds ** 4)
    with open("channel.beam", "w", newline="\n") as f:
        f.write(f"{N - 4}\n")
        for s in range(N - 2):
            c1 = X[s] - 2 * X[s + 1] + X[s + 2]      # x-curvature
            c2 = Y[s] - 2 * Y[s + 1] + Y[s + 2]      # y-curvature
            if s <= n_top - 3 or s >= n_top:
                f.write("%d %d %d %1.16e %1.16e %1.16e\n" % (s, s + 1, s + 2, beam_force, c1, c2))


def plot_geometry(L, X, Y):
    import matplotlib.pyplot as plt
    plt.plot(X, Y, "*")
    plt.axis([-L / 2, L / 2, -L / 2, L / 2])
    plt.title("Channel Flow Geometry")
    plt.xlabel("x")
    plt.ylabel("y")
    plt.show()


X, Y, n_top = get_vertices(L, d, ds)
write_vertices(X, Y)
write_target(X, kappa_target, ds)
write_spring(X, kappa_spring, ds, n_top)
write_beam(X, Y, kappa_beam, ds, n_top)
if "--plot" in sys.argv:
    plot_geometry(L, X, Y)
