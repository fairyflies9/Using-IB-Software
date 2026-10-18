"""visit_queries.py: the data-analysis recipes of chapter 29 (a box, queries over time, a pick over time, a lineout,
curves exported as text), scripted for VisIt 3.5.

Run INSIDE VisIt's Python (no GUI):
    visit -nowin -cli -s visit_queries.py -- <dumps.visit> <out dir> [key=value ...]
keys (the defaults are the 2019 deck's numbers, which fit IB/11's top vessel: centre line y = 0.15, diameter 0.1):
    box=0,0.01,0.10,0.20      xmin,xmax,ymin,ymax of the Box for the average over time
    point=0,0.15              the pick point
    line=0,0.10,0,0.20        the lineout's ends x0,y0,x1,y1; the flux counts the velocity across it, positive to the
                              right of the direction from (x0,y0) to (x1,y1) (+x for a line drawn upwards)
    samples=50                lineout samples ("the default number of 50 is typically pretty good")
    lineout_state=-1          the frame of the lineout (-1: the last)
It writes PNGs of the box and of each curve window, the curves as VisIt .curve text files, averages.csv (for every
frame t: the average of U_x over the box, Query "Average Value" frame by frame, and the flow rate across the line, the
lineout of the velocity across it integrated by the trapezoid rule) and lineouts.csv (every frame's lineout), so the
GUI's curves can be checked number by number. On IB/11 in VisIt 3.5.0 the box average from QueryOverTime came out 8-10 %
lower than the same query frame by frame, whose numbers agree with the flow rate (chapter 29); check a time query
against a few single frames.
"""
import os
import sys
import glob
import time

args = [a for a in sys.argv[1:] if a != "--"]
if len(args) < 2:
    print(__doc__); sys.exit(1)
DB, OUT = args[0], args[1]
opt = dict(a.split("=", 1) for a in args[2:])
BOX = [float(v) for v in opt.get("box", "0,0.01,0.10,0.20").split(",")]
PT = [float(v) for v in opt.get("point", "0,0.15").split(",")]
LN = [float(v) for v in opt.get("line", "0,0.10,0,0.20").split(",")]
NS = int(opt.get("samples", 50))
LSTATE = int(opt.get("lineout_state", -1))
os.makedirs(OUT, exist_ok=True)
LAG = os.path.join(os.path.dirname(DB), "lag_data.visit")


def P(*a):
    print(*a); sys.stdout.flush()


def annotations():
    a = AnnotationAttributes(); a.userInfoFlag = 0; a.databaseInfoFlag = 0; a.timeInfoFlag = 1; a.legendInfoFlag = 1
    SetAnnotationAttributes(a)


def save(name, fmt="PNG", w=1200, h=900):
    """Save the active window. A curve file is looked for afterwards wherever VisIt 3.5 headless put it."""
    s = SaveWindowAttributes(); s.outputToCurrentDirectory = 0; s.outputDirectory = OUT; s.fileName = name
    s.family = 0; s.width, s.height = w, h; s.resConstraint = s.NoConstraint
    s.format = s.CURVE if fmt == "CURVE" else s.PNG
    SetSaveWindowAttributes(s); r = SaveWindow(); P("saved", name, fmt, r)
    return r


def curve_values():
    """The (x, y) points of every curve in the active window, read from its plots."""
    out = []
    for i in range(GetPlotList().GetNumPlots()):
        SetActivePlots(i)
        try:
            out.append(GetPlotInformation()["Curve"])
        except Exception as e:
            P("no curve data for plot", i, e)
    return out


try:
    meshes = []
    if os.path.exists(LAG):                         # open the structure first: no plot of it is made yet
        OpenDatabase(LAG); DeleteAllPlots()
        ml = GetMetaData(LAG); meshes = [ml.GetMeshes(i).name for i in range(ml.GetNumMeshes())]
        P("structure meshes:", meshes)
    OpenDatabase(DB); DeleteAllPlots()              # VisIt adds a Subset plot of 'levels' on opening: remove it
    md = GetMetaData(DB); times = list(md.times); N = md.numStates
    P("database:", DB, N, "frames, t =", times[0], "to", times[-1])
    # your own expressions (IBAMR 0.19 writes U only; and VisIt 3.5's automatic U_magnitude fails beside a second
    # database, chapter 27)
    DefineScalarExpression("U_x", "U[0]"); DefineScalarExpression("U_y", "U[1]"); DefineScalarExpression("speed", "magnitude(U)")
    # the velocity across the line: the unit normal (dy, -dx)/length, to the right of the direction start -> end
    dxl, dyl = LN[2] - LN[0], LN[3] - LN[1]; Ll = (dxl * dxl + dyl * dyl) ** 0.5
    DefineScalarExpression("U_n", "(%.12g)*U[0] + (%.12g)*U[1]" % (dyl / Ll, -dxl / Ll))
    annotations()

    def goto(k):
        for ts in GetTimeSliders():
            SetActiveTimeSlider(ts); SetTimeSliderState(k)

    def box_plot():
        ActivateDatabase(DB)
        AddPlot("Pseudocolor", "U_x"); AddOperator("Box")
        b = BoxAttributes(); b.amount = b.Some; b.minx, b.maxx, b.miny, b.maxy = BOX; b.minz, b.maxz = -1, 1
        SetOperatorOptions(b)
    # ---- 1. the picture: U_x drawn only inside the box, with the structure (the structure only for the picture)
    box_plot()
    ActivateDatabase(LAG) if meshes else None
    for m in meshes:
        if m.endswith("_vertices") and not m.startswith("markers"):
            AddPlot("Mesh", m); ma = MeshAttributes(); ma.legendFlag = 0; SetPlotOptions(ma)
    DrawPlots(); goto(N - 1)
    save("ch29-box")
    DeleteAllPlots()
    # ---- 2. the average of U_x over the box, frame by frame (the numbers) and as a query over time (the curve);
    # only the fluid in the window from here on
    box_plot(); DrawPlots()
    SetActivePlots(0)
    rows = []
    for k in range(N):
        for ts in GetTimeSliders():
            SetActiveTimeSlider(ts); SetTimeSliderState(k)
        SetActivePlots(0)
        Query("Average Value"); avg = GetQueryOutputValue()
        rows.append([times[k], avg])
    P("average U_x in the box: first", rows[0], "last", rows[-1])
    qa = GetQueryOverTimeAttributes(); qa.timeType = qa.DTime; SetQueryOverTimeAttributes(qa)
    SetActivePlots(0)
    t0 = time.time(); QueryOverTime("Average Value"); P("QueryOverTime Average Value", round(time.time() - t0, 1), "s")
    SetActiveWindow(2); annotations()
    save("ch29-average-over-time"); save("ch29-average-over-time", "CURVE")
    avg_curve = curve_values(); P("curve points (average):", len(avg_curve[0]) // 2 if avg_curve else 0)
    DeleteAllPlots(); SetActiveWindow(1)
    # ---- 3. a pick over time at the point: U_x and the speed (on a plot of U_x without the box)
    DeleteAllPlots(); ActivateDatabase(DB); AddPlot("Pseudocolor", "U_x"); DrawPlots()
    goto(0)
    SetActivePlots(0)
    t0 = time.time()
    # U_x is node-centred here: a zone pick through time refuses ("centering ... does not match"), a node pick works
    NodePick(coord=(PT[0], PT[1], 0.0), vars=("U_x", "speed"), do_time=1, preserve_coord=1, curve_plot_type=0)
    P("NodePick over time", round(time.time() - t0, 1), "s")
    SetActiveWindow(2); annotations()
    save("ch29-pick-over-time"); save("ch29-pick-over-time", "CURVE")
    pick_curves = curve_values()
    DeleteAllPlots(); SetActiveWindow(1)
    # ---- 4. a lineout across the line at one frame, sampled
    k = LSTATE if LSTATE >= 0 else N - 1
    for ts in GetTimeSliders():
        SetActiveTimeSlider(ts); SetTimeSliderState(k)
    SetActivePlots(0)
    Lineout(start_point=(LN[0], LN[1], 0.0), end_point=(LN[2], LN[3], 0.0), vars=("U_n",), use_sampling=1, num_samples=NS)
    SetActiveWindow(2); annotations()
    save("ch29-lineout"); save("ch29-lineout", "CURVE")
    ln = curve_values()
    # VisIt's own integral of the curve: the flow rate across the line per unit depth
    Query("Integrate"); P("Integrate query on the sampled lineout (frame %d):" % k, GetQueryOutputValue())
    DeleteAllPlots(); SetActiveWindow(1)
    # the same line without sampling: VisIt takes the values where the line crosses the cells
    Lineout(start_point=(LN[0], LN[1], 0.0), end_point=(LN[2], LN[3], 0.0), vars=("U_n",), use_sampling=0)
    SetActiveWindow(2); save("ch29-lineout-nosampling", "CURVE"); c = curve_values()
    P("lineout without sampling: %d points" % (len(c[0]) // 2 if c and c[0] else 0))
    DeleteAllPlots(); SetActiveWindow(1)
    # ---- 5. the flow rate across the line in every frame: the lineout's integral (the profiles kept for plotting)
    flux = []; prof = open(os.path.join(OUT, "lineouts.csv"), "w"); prof.write("t,s,U_n\n")
    for kk in range(N):
        for ts in GetTimeSliders():
            SetActiveTimeSlider(ts); SetTimeSliderState(kk)
        SetActivePlots(0)
        Lineout(start_point=(LN[0], LN[1], 0.0), end_point=(LN[2], LN[3], 0.0), vars=("U_n",), use_sampling=1, num_samples=NS)
        SetActiveWindow(2); c = curve_values(); DeleteAllPlots(); SetActiveWindow(1)
        if c and c[0]:
            xs, ys = c[0][0::2], c[0][1::2]
            q = sum(0.5 * (ys[i] + ys[i + 1]) * (xs[i + 1] - xs[i]) for i in range(len(xs) - 1))
            for x_, y_ in zip(xs, ys):
                prof.write("%.6g,%.6g,%.6g\n" % (times[kk], x_, y_))
        else:
            q = float("nan")
        flux.append(q)
    prof.close()
    with open(os.path.join(OUT, "averages.csv"), "w") as f:
        f.write("t,avg_Ux_box,flow_rate_line\n")
        for (t, a), q in zip(rows, flux):
            f.write("%.6g,%.6g,%.6g\n" % (t, a, q))
    P("flow rate across the line: max", max(flux), "min", min(flux), "mean over the last period", sum(flux[N // 2:]) / len(flux[N // 2:]))
    # where did the .curve files go?
    for pattern in (os.path.join(OUT, "*.curve"), "/tmp/*.curve", os.path.join(os.getcwd(), "*.curve")):
        P("curve files", pattern, sorted(glob.glob(pattern))[-6:])
except Exception as e:
    P("FAILED", e)
finally:
    P("done")
    sys.exit(0)
