// triangle.geo: gmsh script for the triangle of example IBFE/05.
//
// The triangle has corners (0.5,0), (0,0) and (0,0.5), the same as the
// course mesh triangle.msh. The points, lines and surface are numbered as
// gmsh's graphical interface numbered them when the course mesh was made.
//
// Make a mesh file that libMesh can read (ASCII text, MSH format 2.2):
//
//   gmsh -2 -format msh22 triangle.geo -o triangle_gmsh.msh
//
// libMesh reads ASCII MSH files (format 2.2 or 4.1) but not binary ones.

// Target element size: about one finest grid cell, DX = L/NFINEST = 2/128.
lc = 0.0156;

// 2D meshing algorithm: 5 is Delaunay. With it, gmsh 4.12 makes the same
// numbers of nodes and triangles as the course mesh (759 and 1404). Without
// this line gmsh 4 uses Frontal-Delaunay (6): 687 nodes and 1260 triangles.
Mesh.Algorithm = 5;

Point(1) = {0.5, 0.0, 0.0, lc};
Point(2) = {0.0, 0.0, 0.0, lc};
Point(3) = {0.0, 0.5, 0.0, lc};

Line(1) = {3, 2};          // left side, on x = 0
Line(2) = {2, 1};          // bottom side, on y = 0
Line(3) = {3, 1};          // the long side

Curve Loop(4) = {1, 2, -3};  // "Line Loop" in gmsh 3 and older
Plane Surface(5) = {4};

// Once a file has any physical group, gmsh saves only the elements that
// belong to a physical group. A 2D mesh therefore needs a Physical Surface.
// A file with only a Physical Curve would hold just the boundary lines.
Physical Surface("triangle", 1) = {5};
