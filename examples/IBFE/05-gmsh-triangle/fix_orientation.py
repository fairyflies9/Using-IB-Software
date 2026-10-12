#!/usr/bin/env python3
"""Make every triangle of a 2D gmsh mesh counterclockwise.

IBAMR stops with "IBAMR requires that the Jacobian of each element must be
positive" if a triangle's nodes are listed clockwise. gmsh lists them
clockwise when the curve loop of the surface goes around clockwise.

Usage:
    python3 fix_orientation.py old.msh new.msh

The input must be an ASCII gmsh file in MSH format 2.2 (gmsh -format msh22).
For each 3-node triangle (gmsh element type 2) whose nodes go clockwise, the
last two nodes are swapped. Nothing else in the file changes. This is how
triangle.msh was made from the course version of the mesh, whose 1404
triangles were all clockwise.
"""
import sys


def main(old_name, new_name):
    # The second line of a gmsh file is "version file-type data-size", and
    # file-type is 0 for ASCII and 1 for binary.
    with open(old_name, "rb") as f:
        header = [f.readline().decode("ascii", "replace").strip() for _ in range(2)]
    if header[0] != "$MeshFormat" or not header[1].startswith("2"):
        sys.exit("%s is not a gmsh file in MSH format 2.2" % old_name)
    if header[1].split()[1] != "0":
        sys.exit("%s is a binary gmsh file; save it as ASCII text" % old_name)
    with open(old_name) as f:
        lines = f.read().split("\n")

    # Node coordinates, by node number.
    i = lines.index("$Nodes")
    xy = {}
    for k in range(int(lines[i + 1])):
        p = lines[i + 2 + k].split()
        xy[int(p[0])] = (float(p[1]), float(p[2]))

    # Elements: "number type ntags tag1 ... node1 node2 ...".
    j = lines.index("$Elements")
    n_tri = n_flipped = 0
    for k in range(int(lines[j + 1])):
        p = lines[j + 2 + k].split()
        if p[1] != "2":
            continue
        n_tri += 1
        first = 3 + int(p[2])  # position of the first node number
        a, b, c = (xy[int(v)] for v in p[first:first + 3])
        twice_area = (b[0] - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (b[1] - a[1])
        if twice_area < 0.0:
            p[first + 1], p[first + 2] = p[first + 2], p[first + 1]
            lines[j + 2 + k] = " ".join(p)
            n_flipped += 1

    # newline="\n" keeps Unix line endings, also when run on Windows.
    with open(new_name, "w", newline="\n") as f:
        f.write("\n".join(lines))
    print("%s: %d triangles, %d were clockwise and were flipped; wrote %s"
          % (old_name, n_tri, n_flipped, new_name))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
