"""beam_ibfe_mesh2d.py: writes IBFE_Mesh2D_128.poly, a Triangle input file for
the outline of a 1.0 by 0.25 rectangle. Python version of Beam_IBFE_Mesh2D.m;
it writes the same file. Run it from this folder:  python3 beam_ibfe_mesh2d.py

Triangle (https://www.cs.cmu.edu/~quake/triangle.html) turns the outline into
a triangle mesh, for example with  triangle -pq IBFE_Mesh2D_128.poly
Point numbers in a .poly file start at 1.
"""
L = 2.0                                     # length of computational domain (m)
MAX_LEVELS = 2                              # maximum number of levels in locally refined grid
REF_RATIO = 4                               # refinement ratio between levels
NCOARSE = 32                                # actual number of grid cells on coarsest grid level
N = REF_RATIO ** (MAX_LEVELS - 1) * NCOARSE # effective number of grid cells on finest grid level
dx = 1.0 * L / N                            # Cartesian mesh width (m)
ds = dx * 2                                 # spacing of the outline points

# Outline points, in the same order as the MATLAB script:
# top edge (33 points), bottom edge (33), right side (7), left side (7).
top_x = [-0.5 + k * ds for k in range(33)]           # -0.5:ds:0.5
side_y = [(-0.125 + ds) + k * ds for k in range(7)]  # (-0.125+ds):ds:(0.125-ds)
x_points = top_x + top_x + [0.5] * 7 + [-0.5] * 7
y_points = [0.125] * 33 + [-0.125] * 33 + side_y + side_y
p = len(x_points)                                    # 80 points

# Edges (facets) joining the points into one closed outline, numbered from 1
facets = []
facets += [(i, i + 1) for i in range(1, 33)]     # top edge: 1-2, ..., 32-33
facets += [(i, i + 1) for i in range(34, 66)]    # bottom edge: 34-35, ..., 65-66
facets += [(i, i + 1) for i in range(67, 73)]    # right side: 67-68, ..., 72-73
facets += [(i, i + 1) for i in range(74, 80)]    # left side: 74-75, ..., 79-80
facets += [(1, 80), (33, 73), (34, 74), (66, 67)]  # corners to the sides

mesh_name = "IBFE_Mesh2D_"
with open(f"{mesh_name}{N}.poly", "w", newline="\n") as f:
    # points: count, dimension 2, no attributes, one boundary marker
    f.write("%d %d %d %d \n \n" % (p, 2, 0, 1))
    for j in range(p):
        f.write("%d %1.16e %1.16e %d\n" % (j + 1, x_points[j], y_points[j], 1))
    # segments: count, one boundary marker
    f.write("\n%d %d\n" % (len(facets), 1))
    for j, (a, b) in enumerate(facets, start=1):
        f.write("%d %d %d %d\n" % (j, a, b, 1))
    # holes: none
    f.write("\n%d \n" % 0)
