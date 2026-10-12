"""generate_mesh2d.py: writes bristles1024.vertex and bristles1024.target for
example IB/04 (Using IB Software). Python version of generate_mesh2d.m. Run it
from this folder:
    python3 generate_mesh2d.py

The course folder had no generator for these files. This script and
generate_mesh2d.m were written in 2026 to reproduce them (see README.md for
the one last-digit difference between MATLAB and Python).

The structure is a row of 9 small cylinders ("bristles") along the x axis,
0.05 m apart, with the middle one centered on the origin. Every point is a
target point, and update_target_point_positions.cpp moves the targets.
Point indices in the IBAMR files start at 0.
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 1024                                      # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

radius = 0.0025                               # cylinder radius (m)
spacing = 0.05                                # distance between neighboring cylinder centers (m)
ncyl = 9                                      # number of cylinders
npts = math.ceil(2 * (2 * math.pi * radius / L) * N)  # number of points on each cylinder (33)
dtheta = 2 * math.pi / npts                   # angle between neighboring points on a cylinder

mesh_name = "bristles"                        # structure name
kappa_target = 4.096e6                        # target point stiffness written to the .target file

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information, one cylinder after another from left to
# right. On each cylinder the angle goes from dtheta to 2*pi, so the last
# point of each cylinder is the one on its right side.
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % (ncyl * npts))
    for c in range(ncyl):
        center_x = (c - (ncyl - 1) / 2) * spacing   # -0.2, -0.15, ..., 0.2
        for s in range(1, npts + 1):
            x = center_x + radius * math.cos(s * dtheta)
            y = radius * math.sin(s * dtheta)
            f.write("%1.16e %1.16e\n" % (x, y))

# Write out the target point information: every point is a target point.
with open(f"{mesh_name}{N}.target", "w", newline="\n") as f:
    f.write("%d\n" % (ncyl * npts))
    for s in range(ncyl * npts):
        f.write("%d %1.16e\n" % (s, kappa_target))
