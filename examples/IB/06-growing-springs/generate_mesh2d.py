"""generate_mesh2d.py: writes wing_512.vertex and wing_512.spring for example
IB/06 (Using IB Software). Python version of generate_mesh2d.m; it writes the
same files. Run it from this folder:
    python3 generate_mesh2d.py

The course folder had no generator for these files. This script and
generate_mesh2d.m were written in 2026 and write the same numbers as the course
files.

The structure (called "wing" for historical reasons) is a straight fiber of
length 0.1 m on the x axis, from x = 0.1 (point 0) to x = 0 (the last
point). Its points are joined by springs only: there are no beams, so the
fiber has no bending stiffness. update_springs.cpp makes the springs' rest
lengths grow during the run.
Point indices in the IBAMR files start at 0.
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

fiber_length = 0.1                            # fiber length (m)
npts = math.ceil(2 * (fiber_length / L) * N)  # number of points along the fiber (103)
ds = fiber_length / (npts - 1)                # physical distance between neighboring Lagrangian mesh points (m)

mesh_name = "wing_"                           # structure name
kappa_spring = 2.0e3                          # stretching stiffness K (tension per unit strain).
                                              # The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % npts)
    for s in range(npts):
        x = fiber_length - s * ds
        y = 0.0
        f.write("%1.16e %1.16e\n" % (x, y))

# Write out the spring information: one spring between each pair of
# neighbors, with rest length ds (the starting spacing). The first point of
# each spring (the lower index) is its "master" point.
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 1))
    for s in range(npts - 1):
        f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, kappa_spring * ds / (ds ** 2), ds))
