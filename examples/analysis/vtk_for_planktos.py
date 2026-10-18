"""vtk_for_planktos.py: VisIt's resampled VTK exports of a 3D IBAMR run -> the files Planktos reads (chapter 35).

    python vtk_for_planktos.py <folder of U_####.vtk> <out folder> [variable, default U]

Planktos's Environment.read_IBAMR3d_vtk_data(<out folder>) reads IBAMR_db_000.vtk, IBAMR_db_001.vtk, ...: legacy VTK
RECTILINEAR_GRID files whose point data has the velocity as its active VECTORS, with the time in a TIME field.
VisIt 3.5's export (examples/analysis/resample_export.py, chapter 33) writes the vector instead as a field array
("U 3 <n> double") beside an active scalar (U_c0), and Planktos's reader then stops with
"AttributeError: 'NoneType' object has no attribute 'GetDataType'". This copies each file with the vector made the
active one, keeping the grid, TIME and CYCLE, numbered from 000 in the order of the input names. Needs the vtk module
(Planktos needs it too). VTK 9.4 may print "Could not read dimensions or extents from the file" while it reads the
header of a binary export (and Planktos's reader again on the converted file); the grid comes out whole: the script
prints its size.
"""
import glob
import os
import sys

import vtk

if len(sys.argv) < 3:
    sys.exit(__doc__)
src, dst = sys.argv[1], sys.argv[2]
var = sys.argv[3] if len(sys.argv) > 3 else "U"
files = sorted(glob.glob(os.path.join(src, var + "_*.vtk")))
if not files:
    sys.exit("no %s_*.vtk files in %s" % (var, src))
os.makedirs(dst, exist_ok=True)
for i, f in enumerate(files):
    r = vtk.vtkRectilinearGridReader()
    r.SetFileName(f)
    r.ReadAllScalarsOn(); r.ReadAllVectorsOn(); r.ReadAllFieldsOn()
    r.Update()
    g = r.GetOutput()
    a = g.GetPointData().GetArray(var)
    if a is None or a.GetNumberOfComponents() != 3:
        sys.exit("%s: no 3-component point array %s (a 3D export of the vector is needed)" % (f, var))
    g.GetPointData().SetVectors(a)
    out = os.path.join(dst, "IBAMR_db_%03d.vtk" % i)
    w = vtk.vtkRectilinearGridWriter()
    w.SetFileName(out); w.SetInputData(g); w.SetFileTypeToBinary(); w.Write()
    t = g.GetFieldData().GetArray("TIME")
    print("%s -> %s  (t = %s, %d x %d x %d points)" % (os.path.basename(f), os.path.basename(out),
                                                      t.GetValue(0) if t is not None else "?", *g.GetDimensions()))
