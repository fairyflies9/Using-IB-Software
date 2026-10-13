"""generate_mesh2d.py: writes the structure files for example IB/12 (spider
ballooning, Using IB Software): a vertical dragline of springs and (very weak)
beams with a point mass at its lower end, which the penalty IB method lets fall
under gravity.

The 2020 lecture: "a mass is attached to the bottom of a string. The string
resists bending (a little) and stretching and is massless. This is a simplified
model of spider ballooning. The spider is represented as the point mass. The
silk drag line is the string (massless). The spider falls to the bottom of the
domain due to gravity. The dragline slows it down." "Note that this is a 2D
simulation. The mass is actually a mass per unit length."

Changes from the course generator (8-AddingMass-Spider, 2020): the beam loop
ran one triple too far (it wrote a beam with a point index past the end of the
dragline, under a header that did not count it); the mass point is the last
point of the dragline (point npts-1; the course file said npts-2); the files
have Unix line endings.

Run it in this folder: python3 generate_mesh2d.py
generate_mesh2d.m writes the same files (checked with Octave 8.4 and Python 3.12).
"""
import math

L = 0.3                                       # width of the computational domain (m); it is 0.3 by 0.6
N = 256                                       # number of Cartesian grid meshwidths across the width at the finest level
dx = L / N                                    # Cartesian mesh width (m)

drag_length = 0.10                            # length of the dragline (m)
npts = math.ceil(2 * (drag_length / L) * N)   # number of points along the dragline (172)
ds = drag_length / (npts - 1)                 # distance between neighboring points (m)

mesh_name = "spider2d_"                       # structure name
x_line = 0.15                                 # x of the dragline (m): the middle of the width
y_top = 0.45 + 0.5 * drag_length              # y of the top of the dragline (m); the mass hangs 0.1 m below

kappa_spring = 2.0e1                          # stretching stiffness of the dragline (N); the file stores it as is
kappa_beam = 5.0e-15                          # bending stiffness (N m^2): "resists bending (a little)"; the file stores kappa_beam/ds^2
mass = 2.0e-5                                 # the spider's mass (kg per unit depth): "I had to estimate what a 2D spider sheet would weigh"
kappa_mass = kappa_spring                     # the penalty spring that ties the mass point to its massive copy (N/m)

# newline="\n" gives Unix line endings even on Windows, as IBAMR needs.

# Write out the vertex information: point 0 is the top of the dragline and
# point npts-1 is the bottom, where the spider is.
with open(f"{mesh_name}{N}.vertex", "w", newline="\n") as f:
    f.write("%d\n" % npts)
    for s in range(npts):
        f.write("%1.16e %1.16e\n" % (x_line, y_top - s * ds))

# Write out the link information (including connectivity and material parameters).
with open(f"{mesh_name}{N}.spring", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 1))
    for s in range(npts - 1):
        f.write("%d %d %1.16e %1.16e\n" % (s, s + 1, kappa_spring * ds / ds, ds))

# Write out the beam information: one beam for each three consecutive points.
with open(f"{mesh_name}{N}.beam", "w", newline="\n") as f:
    f.write("%d\n" % (npts - 2))
    for s in range(npts - 2):
        f.write("%d %d %d %1.16e\n" % (s, s + 1, s + 2, kappa_beam * ds / (ds ** 3)))

# Write out the mass information: "index mass penalty_stiffness". The point is
# tied to a massive copy of itself by a spring of this stiffness and zero rest
# length; the copy moves by Newton's law under gravity (chapter 13).
with open(f"{mesh_name}{N}.mass", "w", newline="\n") as f:
    f.write("%d\n" % 1)
    f.write("%d %1.16e %1.16e\n" % (npts - 1, mass, kappa_mass * ds / ds))

print("wrote %s%d.vertex (%d points), .spring (%d), .beam (%d), .mass (1 point, %g kg/m); ds = %.6g m, dx = %.6g m"
      % (mesh_name, N, npts, npts - 1, npts - 2, mass, ds, dx))
