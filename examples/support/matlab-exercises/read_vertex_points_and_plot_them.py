"""read_vertex_points_and_plot_them.py: Python version of
read_Vertex_Points_and_Plot_Them.m. Reads NAME.vertex (the first line is the
number of points, then one "x y" pair per line) and plots the points.

    python3 read_vertex_points_and_plot_them.py rubberband
    python3 read_vertex_points_and_plot_them.py rubberband --show

The plot is saved as NAME_vertices.png; --show also opens a window.
"""
import sys
import matplotlib
if "--show" not in sys.argv:
    matplotlib.use("Agg")
import matplotlib.pyplot as plt

args = [a for a in sys.argv[1:] if not a.startswith("--")]
name = args[0] if args else "rubberband"
with open(name + ".vertex") as f:
    lines = [l.split() for l in f if l.strip()]
N = int(float(lines[0][0]))                      # number of Lagrangian points
x = [float(l[0]) for l in lines[1:N + 1]]
y = [float(l[1]) for l in lines[1:N + 1]]

plt.plot(x, y, "r*")
plt.plot(x, y, "bo", fillstyle="none")
plt.savefig(name + "_vertices.png", dpi=150)
print("%d points read from %s.vertex" % (N, name))
if "--show" in sys.argv:
    plt.show()
