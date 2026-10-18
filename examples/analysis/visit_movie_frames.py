"""visit_movie_frames.py: the frames of a movie of an IBAMR run, one PNG per dump, from VisIt 3.5 without a window
(chapter 30). Encode them afterwards with make_movie.py (ffmpeg), or keep them as the record of the movie.

Run INSIDE VisIt's Python (no GUI):
    visit -nowin -cli -s visit_movie_frames.py -- <viz folder or its dumps.visit> <out dir> [key=value ...]
keys:
    var=Omega             the Pseudocolor variable of dumps.visit (U[0], magnitude(U), ... work too: they are
                          defined as expressions)
    lim=auto              colour limits, the same for every frame: "auto" = a quarter of the largest |value| at the
                          last frame, symmetric (the 2020 deck's rule); one number L for -L..L; or two numbers lo,hi
    ct=difference         the colour table (difference for a signed field; hot or viridis for a magnitude)
    meshes=all            the structures to draw, comma separated names from lag_data.visit; "all" = every
                          <name>_mesh, and <name>_vertices for structures without one; "none" for the fluid alone
    window=               the view, xmin,xmax,ymin,ymax (default: VisIt's, the whole domain)
    size=1200x800         the frame size in pixels (even numbers: H.264 needs them)
    start=0 end=-1 every=1  which dumps (end -1: the last)
    time=1                a text annotation "t = <time> s" at the top right (0: none)
    legend=1              the colour bar (0: none)
    prefix=f              frames are <prefix>0000.png, <prefix>0001.png, ... numbered without gaps
    first=0               the number of the first frame: for a run in chunks, start=100 end=199 first=100 (frames.csv
                          is then appended to); otherwise every chunk would start again at <prefix>0000.png
    session=              also save a VisIt session of the first frame here, for `visit -movie -sessionfile`
It writes the frames and frames.csv (frame number, dump index, time). VisIt opens a SAMRAI database with a Subset plot
of the refinement levels already in it (the coloured lines in old movies); this script deletes it.
"""
import os
import sys
import time

args = []
for a in sys.argv[1:]:
    if a in ("-engineargs", "-launchengine"):    # VisIt appends these when started with -np (a parallel engine)
        break
    if a != "--":
        args.append(a)
if len(args) < 2:
    print(__doc__); sys.exit(1)
SRC, OUT = args[0], args[1]
opt = dict(a.split("=", 1) for a in args[2:])
VAR = opt.get("var", "Omega")
CT = opt.get("ct", "difference")
SIZE = [int(v) for v in opt.get("size", "1200x800").lower().split("x")]
START, END, EVERY = int(opt.get("start", 0)), int(opt.get("end", -1)), int(opt.get("every", 1))
PREFIX = opt.get("prefix", "f")
FIRST = int(opt.get("first", 0))
DB = SRC if SRC.endswith(".visit") else os.path.join(SRC, "dumps.visit")
LAG = os.path.join(os.path.dirname(DB), "lag_data.visit")
os.makedirs(OUT, exist_ok=True)


def P(*a):
    print(*a); sys.stdout.flush()


def set_states(k):
    """Every time slider to state k (the fluid and the structure have one each, plus their correlation)."""
    for ts in GetTimeSliders():
        SetActiveTimeSlider(ts); SetTimeSliderState(k)


try:
    meshes = []
    if opt.get("meshes", "all") != "none" and os.path.exists(LAG):
        OpenDatabase(LAG); DeleteAllPlots()          # the structure first: no plot of it is made yet
        ml = GetMetaData(LAG); names = [ml.GetMeshes(i).name for i in range(ml.GetNumMeshes())]
        if opt.get("meshes", "all") == "all":
            meshes = [n for n in names if n.endswith("_mesh")]
            meshes += [n for n in names if n.endswith("_vertices") and n[:-9] + "_mesh" not in names]
        else:
            meshes = opt["meshes"].split(",")
        P("structure:", meshes, "of", names)
    OpenDatabase(DB); DeleteAllPlots()               # removes the Subset plot of 'levels' VisIt adds on opening
    md = GetMetaData(DB); times = list(md.times); N = md.numStates
    end = N - 1 if END < 0 else min(END, N - 1)
    states = list(range(START, end + 1, EVERY))
    P("database:", DB, N, "dumps, t =", times[0], "to", times[-1], "; frames for", len(states), "of them")
    if "[" in VAR or "(" in VAR:                     # U[0], magnitude(U), ...: your own expression
        DefineScalarExpression("movie_var", VAR); var = "movie_var"
    else:
        var = VAR
    a = AnnotationAttributes(); a.userInfoFlag = 0; a.databaseInfoFlag = 0; a.timeInfoFlag = 0
    a.legendInfoFlag = int(opt.get("legend", 1)); a.axes2D.visible = 0
    SetAnnotationAttributes(a)
    if int(opt.get("time", 1)):
        # the time is drawn only on the database line, which is off; a text annotation shows it alone
        t = CreateAnnotationObject("Text2D"); t.text = "t = $time s"; t.position = (0.72, 0.92); t.height = 0.035
    AddPlot("Pseudocolor", var); DrawPlots()
    lim = opt.get("lim", "auto")
    if lim == "auto":
        set_states(states[-1]); Query("MinMax"); mm = GetQueryOutputValue()
        big = max(abs(v) for v in mm); lo, hi = -0.25 * big, 0.25 * big
        P("%s at the last frame: min %g, max %g; limits %g .. %g" % (var, mm[0], mm[1], lo, hi))
    elif "," in lim:
        lo, hi = [float(v) for v in lim.split(",")]
    else:
        lo, hi = -float(lim), float(lim)
    p = PseudocolorAttributes(); p.colorTableName = CT; p.centering = p.Nodal
    p.minFlag = 1; p.min = lo; p.maxFlag = 1; p.max = hi; p.legendFlag = int(opt.get("legend", 1))
    SetPlotOptions(p)
    if meshes:
        ActivateDatabase(LAG)
        for m in meshes:
            AddPlot("Mesh", m); ma = MeshAttributes(); ma.legendFlag = 0
            ma.meshColorSource = ma.MeshCustom; ma.meshColor = (0, 0, 0, 255); SetPlotOptions(ma)
        DrawPlots()
    if opt.get("window"):
        v = GetView2D(); v.windowCoords = tuple(float(x) for x in opt["window"].split(",")); SetView2D(v)
    s = SaveWindowAttributes(); s.outputToCurrentDirectory = 0; s.outputDirectory = OUT
    s.family = 0; s.format = s.PNG; s.width, s.height = SIZE; s.resConstraint = s.NoConstraint
    t0 = time.time()
    csv = os.path.join(OUT, "frames.csv")
    new = FIRST == 0 or not os.path.exists(csv)
    with open(csv, "w" if new else "a") as f:
        if new:
            f.write("frame,dump,t\n")
        for n, k in enumerate(states):
            set_states(k)
            s.fileName = "%s%04d" % (PREFIX, FIRST + n); SetSaveWindowAttributes(s); SaveWindow()
            f.write("%d,%d,%.6g\n" % (FIRST + n, k, times[k]))
    P("%d frames in %.1f s -> %s" % (len(states), time.time() - t0, OUT))
    if opt.get("session"):
        set_states(states[0]); SaveSession(opt["session"]); P("session saved:", opt["session"])
except Exception as e:
    P("FAILED", e)
finally:
    sys.exit(0)
