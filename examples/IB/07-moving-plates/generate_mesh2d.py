"""generate_mesh2d.py: writes the structure files of both plates for example
IB/07 (Using IB Software): plate2d_left_512.* and plate2d_rght_512.*
(.vertex, .spring, .beam and .target). Python version of generate_mesh2d.m;
it writes the same files. Run it from this folder:
    python3 generate_mesh2d.py

Each plate is a straight vertical line of points of length 0.1 m, joined by
springs and beams, and every point is a target point. The plates start
5 mm apart, on either side of the origin.
Point indices in the IBAMR files start at 0, separately for each plate.
"""
import math

L = 1.0                                       # length of computational domain (m)
N = 512                                       # number of Cartesian grid meshwidths at the finest level of the AMR grid
dx = L / N                                    # Cartesian mesh width (m)

plate_length = 0.1                            # plate length (m)
npts = math.ceil(2 * (plate_length / L) * N)  # number of points along each plate (103)
ds = plate_length / (npts - 1)                # physical distance between neighboring Lagrangian mesh points (m)

mesh_names = ["plate2d_left_", "plate2d_rght_"]  # structure names
offsets = [-2.5e-3, +2.5e-3]                  # x position of each plate (m)

kappa_spring = 2.0e3                          # stretching stiffness K (tension per unit strain).
                                              # The .spring file stores K/ds, written below as kappa_spring*ds/(ds^2).
kappa_beam = 5.0e-3                           # bending stiffness. The .beam file stores kappa_beam/ds^3,
                                              # written below as kappa_beam*ds/(ds^4).
kappa_target = kappa_spring                   # target point stiffness. The .target file stores kappa_target/ds.

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.
for mesh_name, offset in zip(mesh_names, offsets):

    # Write out the vertex information: point 0 is the top end (y = 0.05).
    with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
        f.write("%d\n" % npts)
        for s in range(npts):
            x = offset
            y = 0.0 + 0.5 * plate_length - s * ds
            f.write("%1.16e %1.16e\n" % (x, y))

    # Write out the spring information
    with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
        f.write("%d\n" % (npts - 1))
        for s in range(npts - 1):
            f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, kappa_spring * ds / (ds ** 2), ds))

    # Write out the beam information
    with open(f"{mesh_name}{N}.beam", "w", newline="\n") as f:
        f.write("%d\n" % (npts - 2))
        for s in range(npts - 2):
            f.write("%d %d %d %1.16e\n" % (s, s + 1, s + 2, kappa_beam * ds / (ds ** 4)))

    # Write out the target point information: every point is a target point.
    with open(f"{mesh_name}{N}.target", "w", newline="\n") as f:
        f.write("%d\n" % npts)
        for s in range(npts):
            f.write("%d %1.16e\n" % (s, kappa_target * ds / (ds ** 2)))
