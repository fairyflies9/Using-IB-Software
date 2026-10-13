"""generate_mesh2d.py: writes the structure files for example IB/09 (the curling
beam, Using IB Software): a straight horizontal beam, clamped at its left end
by two target points, whose preferred curvature update_beams.cpp raises from
zero to that of a quarter circle over the first second.

It is the generator of IB/03 (the tethered leaf) turned on its side, with the
two target points moved from the middle to the left end. The .beam file has
four columns (no preferred curvature), so the beams start straight; the
program sets the curvature before every time step.

Run it in this folder: python3 generate_mesh2d.py
generate_mesh2d.m writes the same files (checked with Octave 8.4 and Python 3.12).
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

beam_length = 0.1                             # beam length (m)
npts = math.ceil(2 * (beam_length / L) * N)   # number of points along the beam (103)
ds = beam_length / (npts - 1)                 # physical distance between neighboring Lagrangian mesh points (m)

mesh_name = "beam_"                           # structure name
x_base = -0.05                                # x position of the clamped end (m); the beam runs to the right
y_base = 0.0                                  # y position of the beam (m)

kappa_spring = 3.0e1                          # stretching stiffness K (tension per unit strain).
                                              # The .spring file stores kappa_spring/ds.
kappa_beam = 2.0e-2                           # bending stiffness (4x the leaf of IB/03). The .beam file stores kappa_beam/ds^3,
                                              # and the force on a point is that times the second difference of X.
kappa_target = kappa_spring                   # target point stiffness. The .target file stores kappa_target/ds.

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information: point 0 is the clamped left end and point
# npts-1 is the free right end.
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % npts)
    for s in range(npts):
        x = x_base + s * ds
        y = y_base
        f.write("%1.16e %1.16e\n" % (x, y))

# Write out the link information (including connectivity and material parameters).
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 1))
    for s in range(npts - 1):
        f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, kappa_spring * ds / (ds ** 2), ds))

# Write out the beam information: each line is "i-1 i i+1 stiffness". A fifth
# and sixth column would be the preferred curvature (C1, C2); left out, it is
# zero, and update_beams.cpp sets it in the program.
with open(f"{mesh_name}{N}.beam", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 2))
    for s in range(npts - 2):
        f.write("%d %d %d %1.16e\n" % (s, s + 1, s + 2, kappa_beam * ds / (ds ** 4)))

# Write out the target point information: the two points at the clamped end,
# 0 and 1, are tethered to where they start, which fixes the end's position
# and its direction.
with open(f"{mesh_name}{N}.target", "w", newline="\n") as f:
    f.write("%d\n" % 2)
    f.write("%d %1.16e\n" % (0, kappa_target * ds / (ds ** 2)))
    f.write("%d %1.16e\n" % (1, kappa_target * ds / (ds ** 2)))

print("wrote %s%d.vertex (%d points), .spring (%d), .beam (%d), .target (2); ds = %.6g m, dx = %.6g m"
      % (mesh_name, N, npts, npts - 1, npts - 2, ds, dx))
