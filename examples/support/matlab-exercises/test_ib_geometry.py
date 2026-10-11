"""test_ib_geometry.py: Python version of test_IB2d_IBAMR_Geometry.m.

Checks a structure before you run it: figure 1 shows the Lagrangian points
with their index numbers, figure 2 adds the spring connections (alternating
red and blue so that neighboring springs are easy to tell apart).

    python3 test_ib_geometry.py                    # rubberband.vertex/.spring, IB2d numbering
    python3 test_ib_geometry.py NAME --ibamr       # NAME.vertex/.spring, IBAMR numbering
    python3 test_ib_geometry.py NAME --show        # also open the figures

IB2d numbers points from 1 and IBAMR (C++) from 0; --ibamr labels the points
from 0 and reads the spring indices that way. The figures are saved as
NAME_points.png and NAME_springs.png.
"""
import sys
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


def read_rows(filename):
    """Return the rows after the first line (the first line holds the count)."""
    with open(filename) as f:
        lines = [l.split() for l in f if l.strip()]
    count = int(float(lines[0][0]))
    rows = [[float(v) for v in l] for l in lines[1:count + 1]]
    return rows


def plot_points(xy, labels):
    for (x, y), lab in zip(xy, labels):
        plt.plot(x, y, "k.", markersize=12)
        plt.text(x, y, "  %d" % lab)
    plt.xlabel("x")
    plt.ylabel("y")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    name = args[0] if args else "rubberband"
    ibamr = "--ibamr" in sys.argv
    first = 0 if ibamr else 1                       # index of the first point

    xy = [(r[0], r[1]) for r in read_rows(name + ".vertex")]
    springs = [(int(r[0]) - first, int(r[1]) - first) for r in read_rows(name + ".spring")]
    labels = range(first, first + len(xy))

    plt.figure(1)
    plot_points(xy, labels)
    plt.savefig(name + "_points.png", dpi=150)

    plt.figure(2)
    for i, (a, b) in enumerate(springs):            # leader a, follower b (0-based here)
        color = "r-" if i % 2 == 0 else "b-"
        plt.plot([xy[a][0], xy[b][0]], [xy[a][1], xy[b][1]], color, linewidth=2)
    plot_points(xy, labels)
    plt.savefig(name + "_springs.png", dpi=150)
    print("%d points, %d springs" % (len(xy), len(springs)))
    if "--show" in sys.argv:
        plt.show()
