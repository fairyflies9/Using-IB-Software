"""resample_export.py: VisIt's own route from the adaptive grid to a uniform one, scripted (chapter 33).

Run INSIDE VisIt's Python (no GUI):
    visit -nowin -cli -s resample_export.py -- <dumps.visit> <variable> <out dir> [options]
options (key=value):
    nx=60 ny=30 nz=1          samples per direction (nz=1 picks a plane in 3D; give z0 for its position)
    x0=.. x1=.. y0=.. y1=.. z0=.. z1=..   the box to sample (default: the whole domain, VisIt's "Resample entire extents")
    states=all | 10 | 10:20   which time states (0-based; the default is all)
    format=ascii | binary     legacy VTK ASCII (readable by eye and by every reader) or binary
It writes <out dir>/<variable>_<state>.vtk (RECTILINEAR_GRID; VisIt 3.5 headless drops the file name it is given
and writes <dir>/.vtk, so each export is renamed right after it is written) and prints one line per state.

This is the 2017-2018 recipe of the "Taking a 2D slice from 3D IBAMR" and "Resampling AMR grids" decks
(Operators > Geometry > Resample, File > Export Database > VTK, a loop over time) and of C. Strickland's
read_IBAMR3d_py27.py (2017), written for VisIt 3.x and Python 3. Where the AMR grid is coarse (the edges of a
box) the resampled values away from any patch are set to defaultValue (0): cut those edges off in the analysis.
"""
import os
import sys
import time

args = [a for a in sys.argv[1:] if a != "--"]
if len(args) < 3:
    print(__doc__); sys.exit(1)
db, var, out = args[0], args[1], args[2]
opt = dict(a.split("=", 1) for a in args[3:])
nx, ny, nz = int(opt.get("nx", 60)), int(opt.get("ny", 30)), int(opt.get("nz", 1))
fmt = opt.get("format", "ascii")
os.makedirs(out, exist_ok=True)

OpenDatabase(db)
DeleteAllPlots()                                    # VisIt adds a Subset plot of 'levels' on open: remove it
md = GetMetaData(db)
mesh = md.GetMeshes(0)
is3d = mesh.spatialDimension == 3
nstates = md.numStates
is_vector = any(md.GetVectors(i).name == var for i in range(md.GetNumVectors()))
# A Pseudocolor plot of a scalar carries the resampled grid, and the export adds every variable asked for, resampled
# too (checked: u = U[0], v, Omega and the vector U all came out equal to the reader's values). A Vector plot
# exported this way gave a file with empty coordinate lists in 3.5.0, and a Pseudocolor of the automatic
# U_magnitude expression gave zeros for U, so for a vector the plot is a Pseudocolor of its first component.
if is_vector:
    DefineScalarExpression(var + "_c0", var + "[0]")
    AddPlot("Pseudocolor", var + "_c0")
else:
    AddPlot("Pseudocolor", var)
DrawPlots()
# The domain: a SAMRAI database's metadata extents are all zero in 3.5.0 (a resample over them is empty and exports
# zeros), so ask the drawn plot for its extents instead.
Query("SpatialExtents")
ext = [float(v) for v in GetQueryOutputValue()]    # xmin, xmax, ymin, ymax (2D) or ... zmin, zmax (3D)
ext = (ext + [0.0, 0.0])[:6]                        # pad a 2D answer (an IndexError here would leave the CLI waiting)
ext = [ext[0], ext[2], ext[4], ext[1], ext[3], ext[5]]
x0 = float(opt.get("x0", ext[0])); x1 = float(opt.get("x1", ext[3]))
y0 = float(opt.get("y0", ext[1])); y1 = float(opt.get("y1", ext[4]))
z0 = float(opt.get("z0", ext[2] if is3d else 0.0)); z1 = float(opt.get("z1", ext[5] if is3d else 0.0))
if nz == 1 and is3d and "z1" not in opt:
    z1 = z0                                         # one plane at z0
# A direction sampled once must still be a thin slab, not a plane of zero thickness: with start == end VisIt 3.5
# resamples nothing and exports zeros (checked on the 3D flow tank). One per cent of the axis is thin enough.
for lo, hi, ns, k in ((x0, x1, nx, "x"), (y0, y1, ny, "y"), (z0, z1, nz, "z")):
    if ns == 1 and hi == lo:
        span = ext[3 + "xyz".index(k)] - ext["xyz".index(k)]
        hi = lo + 0.01 * (span if span > 0 else 1.0)
        if k == "x": x1 = hi
        elif k == "y": y1 = hi
        else: z1 = hi

AddOperator("Resample")
r = ResampleAttributes()
r.useExtents = 0
r.startX, r.endX, r.samplesX = x0, x1, nx
r.startY, r.endY, r.samplesY = y0, y1, ny
r.is3D = 1 if is3d else 0
r.startZ, r.endZ, r.samplesZ = z0, z1, nz
r.tieResolver = r.random
r.defaultValue = 0
r.distributedResample = 1
r.cellCenteredOutput = 0
SetOperatorOptions(r)
DrawPlots()

sel = opt.get("states", "all")
if sel == "all":
    states = list(range(nstates))
elif ":" in sel:
    a, b = sel.split(":"); states = list(range(int(a), int(b) + 1))
else:
    states = [int(sel)]

e = ExportDBAttributes()
e.db_type = "VTK"; e.db_type_fullname = "VTK_1.0"
e.dirname = out; e.variables = (var,); e.allTimes = 0
opts = GetExportOptions("VTK")
opts["FileFormat"] = "Legacy Binary" if fmt == "binary" else "Legacy Ascii"
for s in states:
    SetTimeSliderState(s); DrawPlots()
    mm = Query("MinMax")                            # printed as a check that the plot holds data at this state
    e.filename = "%s_%04d" % (var, s)
    target = os.path.join(out, "%s_%04d.vtk" % (var, s))
    strays = [os.path.join(os.getcwd(), ".vtk"), os.path.join(out, ".vtk")]   # 3.5.0 headless: dirname and filename ignored
    for p in strays + [target]:                     # start clean: an old file would be mistaken for the new one
        if os.path.exists(p):
            os.remove(p)
    ok = ExportDatabase(e, opts)
    for _ in range(100):                            # the engine writes after the call returns
        if os.path.exists(target) or any(os.path.exists(p) for p in strays):
            break
        time.sleep(0.1)
    time.sleep(0.5)
    for p in strays:
        if os.path.exists(p) and not os.path.exists(target):
            os.replace(p, target)
    print("state %d  t = %g  ->  %s  (%s; plot %s)" % (s, md.times[s], target, "ok" if ok else "export failed", mm.replace("\n", " ").strip())); sys.stdout.flush()
sys.exit(0)
