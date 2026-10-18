"""visit_3d.py: the 3D pictures of chapter 27 (VisIt in 3D: isosurfaces, slices, vectors, streamlines), scripted.

Run INSIDE VisIt's Python (no GUI):
    visit -nowin -cli -s visit_3d.py -- plate <viz_IB3d folder of IBFE/10> <out dir>
    visit -nowin -cli -s visit_3d.py -- glyco <viz_IB3d folder of IB/08, run with SHEAR_START = 1> <out dir>
It writes one PNG per picture into <out dir> and prints what it did. Tested with VisIt 3.5.0 (Linux, headless).

Each picture is one recipe of the lectures' "VisIt 3D" slides (2015, 2020, 2021), in VisIt 3.5's names:
  * the immersed boundary: a Mesh plot of the vertices (pixels or spheres), or of the finite element mesh moved by
    the Displace operator;
  * isosurfaces: a Contour plot of the vorticity magnitude (vortmag = magnitude(Omega), defined here: the lectures'
    omega_magnitude), 5-10 levels between a minimum and a maximum you choose, light to dark blue, each 15 % opaque
    (in VisIt 3.5 the opacity is part of each level's colour: the Contour plot has no opacity field of its own);
  * vectors on a slice: a Vector plot (glyphs placed uniformly in space, high quality, one colour, a fixed scale)
    with a Slice operator applied to that plot only; the vorticity on the same slice, as colour or contour lines;
  * ThreeSlice, and streamlines: VisIt 3 has no Streamline plot; streamlines are the IntegralCurve operator, added
    here to a Pseudocolor plot of U.
Most fluid plots get a Box operator first, which cuts them down to the region around the body; the camera is then
set on the body with a focus and a parallel scale (the automatic view frames the whole box). Each picture takes
about a second. VisIt 3.5.0 traps met on the way are commented where they are avoided (search for "3.5").
"""
import os
import sys
import time

args = [a for a in sys.argv[1:] if a != "--"]
if len(args) < 3 or args[0] not in ("plate", "glyco"):
    print(__doc__); sys.exit(1)
CASE, VIZ, OUT = args[0], args[1], args[2]
os.makedirs(OUT, exist_ok=True)
FL = os.path.join(VIZ, "dumps.visit")
BODY = os.path.join(VIZ, "output.ex2" if CASE == "plate" else "lag_data.visit")


def P(*a):
    print(*a); sys.stdout.flush()


def annotations(dark=False, axes=False, time_on=True):
    a = AnnotationAttributes()
    a.userInfoFlag = 0; a.databaseInfoFlag = 0; a.timeInfoFlag = 1 if time_on else 0; a.legendInfoFlag = 1
    a.axes3D.visible = 1 if axes else 0; a.axes3D.bboxFlag = 1 if axes else 0; a.axes3D.triadFlag = 1
    a.backgroundMode = a.Solid
    if dark:
        a.backgroundColor = (0, 0, 0, 255); a.foregroundColor = (255, 255, 255, 255)
    else:
        a.backgroundColor = (255, 255, 255, 255); a.foregroundColor = (0, 0, 0, 255)
    SetAnnotationAttributes(a)


def save(name, w=1400, h=1000):
    s = SaveWindowAttributes(); s.outputToCurrentDirectory = 0; s.outputDirectory = OUT
    s.fileName = name; s.family = 0; s.format = s.PNG; s.width, s.height = w, h; s.resConstraint = s.NoConstraint
    SetSaveWindowAttributes(s); P("saved", name, SaveWindow())


def goto(k):
    """Every time slider (one per open database) to state k."""
    for ts in GetTimeSliders():
        SetActiveTimeSlider(ts); SetTimeSliderState(k)


def view(normal, up=(0, 0, 1), zoom=1.0, focus=None, scale=None, parallel=0):
    """The camera: the direction it looks from (viewNormal), which way is up, and, to frame the body rather than
    the whole box, the point it looks at (focus) and the half-height of the picture (parallelScale)."""
    v = GetView3D(); v.viewNormal = normal; v.viewUp = up; v.imageZoom = zoom; v.perspective = 1 - parallel
    if focus is not None:
        v.focus = focus
    if scale is not None:
        v.parallelScale = scale
    SetView3D(v)


# the region around the body that every fluid plot is cut down to
if CASE == "plate":
    BOX = (-2.0, 6.0, -2.5, 2.5, -2.5, 2.5)
else:
    BOX = (-0.0625, 0.0625, -0.0625, 0.0625, -0.5, -0.25)


def box():
    AddOperator("Box")
    b = BoxAttributes(); b.amount = b.Some
    b.minx, b.maxx, b.miny, b.maxy, b.minz, b.maxz = BOX
    SetOperatorOptions(b)


def body(color=(90, 90, 90, 255), spheres=False, pixels=2, opaque=True):
    """The immersed boundary: the IBFE plate moved by its displacement, or the IB fiber's vertices."""
    ActivateDatabase(BODY)
    if CASE == "plate":
        AddPlot("Mesh", "Mesh")
        m = MeshAttributes(); m.legendFlag = 0; m.meshColorSource = m.MeshCustom; m.meshColor = color
        m.opaqueMode = m.On if opaque else m.Off; m.opaqueColorSource = m.OpaqueCustom; m.opaqueColor = (200, 200, 200, 255)
        SetPlotOptions(m)
        AddOperator("Displace"); d = DisplaceAttributes(); d.variable = "dX"; d.factor = 1.0; SetOperatorOptions(d)
    else:
        AddPlot("Mesh", "glyco_512_vertices")
        m = MeshAttributes(); m.legendFlag = 0; m.meshColorSource = m.MeshCustom; m.meshColor = color
        if spheres:
            m.pointType = m.Sphere; m.pointSize = 0.0008
        else:
            m.pointType = m.Point; m.pointSizePixels = pixels
        SetPlotOptions(m)


BLUES = [(205, 225, 255), (150, 190, 250), (95, 150, 235), (50, 105, 215), (20, 65, 180), (5, 35, 130)]


def iso(var, lo, hi, n=6, alpha=38, colors=BLUES, legend=True):
    AddPlot("Contour", var)
    c = ContourAttributes()
    c.contourMethod = c.Level; c.contourNLevels = n
    c.minFlag = 1; c.min = lo; c.maxFlag = 1; c.max = hi
    # (VisIt 3.5: the Contour plot has no opacity field; the fourth number of each colour is its opacity)
    c.colorType = c.ColorByMultipleColors
    for i in range(n):
        c.SetMultiColor(i, tuple(colors[i % len(colors)]) + (alpha,))
    c.legendFlag = 1 if legend else 0
    SetPlotOptions(c)


def slice_op(axis="y", at=0.0, project=0):
    AddOperator("Slice")
    s = SliceAttributes(); s.originType = s.Intercept; s.originIntercept = at
    s.axisType = {"x": s.XAxis, "y": s.YAxis, "z": s.ZAxis}[axis]; s.project2d = project
    SetOperatorOptions(s)


def vectors(n=4000, color=(30, 30, 30, 255), scale=None, head=0.25):
    """Auto scale off and a fixed scale: on a slice kept in 3D every arrow is then scale times the speed long. On a
    slice projected to 2D (the flat picture) the arrows still came out at different lengths on different refinement
    levels (about 4 times shorter outside the finest level) in VisIt 3.5.0; chapter 27 shows it as a trap."""
    if scale is None:
        scale = 3.0 if CASE == "plate" else 0.4
    AddPlot("Vector", "U")
    # (VisIt 3.5: UniformInSpace works only on a slice projected to 2D; on a slice kept in 3D VisIt warns and adapts)
    va = VectorAttributes(); va.glyphLocation = va.UniformInSpace; va.useStride = 0; va.nVectors = n
    va.geometryQuality = va.High; va.colorByMagnitude = 0; va.vectorColor = color
    va.autoScale = 0; va.scale = scale; va.scaleByMagnitude = 1; va.headSize = head; va.useLegend = 0
    SetPlotOptions(va)


def pseudo(var, lo=None, hi=None, table="hot_desaturated", opacity=1.0, legend=True):
    AddPlot("Pseudocolor", var)
    p = PseudocolorAttributes(); p.colorTableName = table; p.legendFlag = 1 if legend else 0
    if lo is not None:
        p.minFlag = 1; p.min = lo
    if hi is not None:
        p.maxFlag = 1; p.max = hi
    if opacity < 1.0:
        p.opacityType = p.Constant; p.opacity = opacity
    SetPlotOptions(p)


def picture(name, fn):
    t0 = time.time()
    try:
        fn()
    except Exception as e:
        P("ERR", name, e)
    finally:
        DeleteAllPlots()
    P("time", name, round(time.time() - t0, 1), "s")


# ------------------------------------------------------------------ open and inspect
OpenDatabase(FL); DeleteAllPlots()          # VisIt adds a Subset plot of 'levels' when it opens AMR data: remove it
md = GetMetaData(FL)
P("fluid:", md.numStates, "states, t =", round(md.times[0], 4), "to", round(md.times[-1], 4))
P("  vectors", [md.GetVectors(i).name for i in range(md.GetNumVectors())],
  "scalars", [md.GetScalars(i).name for i in range(md.GetNumScalars())])
el = md.GetExprList()
P("  expressions VisIt made", [el.GetExpressions(i).name for i in range(el.GetNumExpressions()) if "time_derivative" not in el.GetExpressions(i).name])
# Your own expressions, not the ones VisIt makes (Omega_magnitude, U_magnitude): in VisIt 3.5.0 a plot of an automatic
# expression, or of the variable operators/IntegralCurve/U, fails ("An invalid variable ... was specified") as soon as a
# plot of a second database (the body) is in the same window; plots of these expressions do not.
DefineScalarExpression("ux", "U[0]")
DefineScalarExpression("omega_y", "Omega[1]")
DefineScalarExpression("vortmag", "magnitude(Omega)")
DefineScalarExpression("speed", "magnitude(U)")
OpenDatabase(BODY); DeleteAllPlots()
mb = GetMetaData(BODY)
P("body:", mb.numStates, "states; meshes", [mb.GetMeshes(i).name for i in range(mb.GetNumMeshes())])
if CASE == "plate":
    DefineVectorExpression("dX", "{dX_0, dX_1, dX_2}")
LAST = md.numStates - 1
annotations()

if CASE == "plate":
    def outside():
        ActivateDatabase(FL); pseudo("speed"); DrawPlots(); goto(LAST)
        annotations(axes=True); view((-0.5, -0.6, 0.6)); save("ch27-plate-outside")
        annotations()
    picture("outside", outside)

    def levels():
        ActivateDatabase(FL); AddPlot("Subset", "levels")
        s = SubsetAttributes(); s.wireframe = 1; s.lineWidth = 1; s.legendFlag = 1; SetPlotOptions(s)
        body(); DrawPlots(); goto(LAST)
        annotations(axes=True); view((-0.5, -0.6, 0.6)); save("ch27-plate-levels")
        annotations()
    picture("levels", levels)

    def iso_light(k=LAST, tag="", LO=0.06):
        def f():
            ActivateDatabase(FL); iso("vortmag", LO, 0.3); box()
            body(); DrawPlots(); goto(k)
            view((-0.55, -0.65, 0.5), focus=(1.5, 0, 0), scale=2.6); save("ch27-plate-iso" + tag)
        return f
    picture("iso", iso_light())
    picture("iso t=0.25", iso_light(LAST // 2, "-t025"))
    picture("iso, minimum too low", iso_light(LAST, "-lowmin", LO=0.01))

    def iso_auto():
        # VisIt's own limits: six levels over the whole range of the data
        ActivateDatabase(FL); AddPlot("Contour", "vortmag"); c = ContourAttributes()
        c.contourMethod = c.Level; c.contourNLevels = 6; c.colorType = c.ColorByMultipleColors
        for i in range(6):
            c.SetMultiColor(i, tuple(BLUES[i]) + (38,))
        SetPlotOptions(c); box(); body(); DrawPlots(); goto(LAST)
        view((-0.55, -0.65, 0.5), focus=(1.5, 0, 0), scale=2.6); save("ch27-plate-iso-auto")
    picture("iso, automatic limits", iso_auto)

    def iso_noise():
        # one isosurface at the low value, with the refinement levels' boxes: where are the fragments?
        ActivateDatabase(FL); AddPlot("Contour", "vortmag"); c = ContourAttributes()
        c.contourMethod = c.Value; c.contourValue = (0.01,); c.colorType = c.ColorBySingleColor
        c.singleColor = (60, 100, 220, 90); c.legendFlag = 0; SetPlotOptions(c); box()
        AddPlot("Subset", "levels"); sa = SubsetAttributes(); sa.wireframe = 1; sa.lineWidth = 2; SetPlotOptions(sa); box()
        body(); DrawPlots(); goto(LAST)
        annotations(axes=True); view((0, 0, 1), up=(0, 1, 0), focus=(1.5, 0, 0), scale=3.0); save("ch27-plate-iso-noise")
        annotations()
    picture("iso noise and levels", iso_noise)

    def iso_dark(LO=0.06):
        ActivateDatabase(FL); iso("vortmag", LO, 0.3); box()
        body(color=(230, 230, 230, 255)); DrawPlots(); goto(LAST)
        annotations(dark=True); view((-0.55, -0.65, 0.5), focus=(1.5, 0, 0), scale=2.6); save("ch27-plate-iso-dark")
        annotations()
    picture("iso dark", iso_dark)

    def iso_single():
        # the lectures' recipe word for word: one colour, about 12 % opaque
        ActivateDatabase(FL); AddPlot("Contour", "vortmag"); c = ContourAttributes()
        c.contourMethod = c.Level; c.contourNLevels = 8; c.minFlag = 1; c.min = 0.06; c.maxFlag = 1; c.max = 0.3
        c.colorType = c.ColorBySingleColor; c.singleColor = (40, 80, 200, 31); c.legendFlag = 0; SetPlotOptions(c)
        box(); body(); DrawPlots(); goto(LAST)
        view((-0.55, -0.65, 0.5), focus=(1.5, 0, 0), scale=2.6); save("ch27-plate-iso-single")
    picture("iso single", iso_single)

    def vec_slice():
        ActivateDatabase(FL)
        pseudo("omega_y", -0.3, 0.3, table="RdBu", opacity=0.7); box(); slice_op("y", 0.0)
        vectors(n=1500); box(); slice_op("y", 0.0)
        body(); DrawPlots(); goto(LAST)
        view((-0.35, -0.9, 0.25), focus=(1.5, 0, 0), scale=2.6); save("ch27-plate-vectors-slice")
    picture("vectors on a slice", vec_slice)

    def contour_slice():
        ActivateDatabase(FL)
        AddPlot("Contour", "omega_y"); c = ContourAttributes(); c.contourMethod = c.Level; c.contourNLevels = 10
        c.minFlag = 1; c.min = -0.3; c.maxFlag = 1; c.max = 0.3; c.colorType = c.ColorByColorTable; c.colorTableName = "RdBu"
        c.lineWidth = 2; SetPlotOptions(c); box(); slice_op("y", 0.0)
        vectors(n=2500, color=(120, 120, 120, 255)); box(); slice_op("y", 0.0)
        body(); DrawPlots(); goto(LAST)
        view((0, -1, 0), focus=(1.5, 0, 0), scale=2.4); save("ch27-plate-contours-slice")
    picture("contours on a slice", contour_slice)

    def flat_slice():
        ActivateDatabase(FL)
        pseudo("omega_y", -0.3, 0.3, table="RdBu"); box(); slice_op("y", 0.0, project=1)
        vectors(n=1200); box(); slice_op("y", 0.0, project=1)
        body(); slice_op("y", 0.0, project=1)
        DrawPlots(); goto(LAST)
        v = GetView2D(); v.windowCoords = (-2.0, 6.0, -2.5, 2.5); SetView2D(v)
        save("ch27-plate-slice-2d", 1400, 900)
    picture("flat slice", flat_slice)

    def three():
        ActivateDatabase(FL); pseudo("ux", 0.0, 0.1)
        AddOperator("ThreeSlice"); t3 = ThreeSliceAttributes(); t3.x = 0.0625; t3.y = 0.0; t3.z = 0.0; SetOperatorOptions(t3)
        body(); DrawPlots(); goto(LAST)
        view((-0.55, -0.65, 0.5), focus=(1.5, 0, 0), scale=2.8); save("ch27-plate-threeslice")
    picture("threeslice", three)

    def stream():
        # (VisIt 3.5: a Pseudocolor of "operators/IntegralCurve/U" fails beside a second database; the operator on U works)
        ActivateDatabase(FL); AddPlot("Pseudocolor", "U"); AddOperator("IntegralCurve")
        ic = IntegralCurveAttributes()
        ic.sourceType = ic.SpecifiedPlane; ic.planeOrigin = (-1.5, 0.0, 0.0); ic.planeNormal = (1, 0, 0); ic.planeUpAxis = (0, 0, 1)
        ic.sampleDistance0 = 3.0; ic.sampleDistance1 = 3.0; ic.sampleDensity0 = 9; ic.sampleDensity1 = 9; ic.fillInterior = 1
        ic.dataValue = ic.Speed; ic.integrationDirection = ic.Forward; ic.maxSteps = 5000
        ic.terminateByDistance = 1; ic.termDistance = 8.0; ic.maxStepLength = 0.05
        ic.issueAdvectionWarnings = 0; ic.issueBoundaryWarnings = 0; ic.issueTerminationWarnings = 0
        ic.issueStepsizeWarnings = 0; ic.issueStiffnessWarnings = 0; ic.issueCriticalPointsWarnings = 0
        SetOperatorOptions(ic)
        p = PseudocolorAttributes(); p.colorTableName = "viridis"; p.lineWidth = 2; SetPlotOptions(p)
        body(); DrawPlots(); goto(LAST)
        view((-0.45, -0.75, 0.45), focus=(2.0, 0, 0), scale=3.0); save("ch27-plate-streamlines")
    picture("streamlines", stream)

else:
    def verts():
        body(pixels=1); DrawPlots(); goto(LAST)
        view((-0.6, -0.7, 0.35), focus=(0, 0, -0.42), scale=0.1); save("ch27-glyco-points", 900, 1100)
    picture("vertices as points", verts)

    def verts_spheres():
        body(spheres=True, color=(40, 90, 200, 255)); DrawPlots(); goto(LAST)
        view((-0.6, -0.7, 0.35), focus=(0, 0, -0.42), scale=0.1); save("ch27-glyco-spheres", 900, 1100)
    picture("vertices as spheres", verts_spheres)

    def outside():
        ActivateDatabase(FL); pseudo("ux"); DrawPlots(); goto(LAST)
        annotations(axes=True); view((-0.6, -0.7, 0.35)); save("ch27-glyco-outside", 900, 1100)
        annotations()
    picture("outside", outside)

    def slice_ux():
        ActivateDatabase(FL); pseudo("ux"); slice_op("y", 0.0)
        body(); DrawPlots(); goto(LAST)
        annotations(axes=True); view((0, -1, 0)); save("ch27-glyco-slice-ux", 900, 1100)
        annotations()
    picture("slice of ux", slice_ux)

    def three():
        ActivateDatabase(FL); pseudo("ux"); box()
        AddOperator("ThreeSlice"); t3 = ThreeSliceAttributes(); t3.x = 0.0; t3.y = 0.0; t3.z = -0.42; SetOperatorOptions(t3)
        body(); DrawPlots(); goto(LAST)
        view((-0.6, -0.7, 0.35), focus=(0, 0, -0.4), scale=0.13); save("ch27-glyco-threeslice", 1000, 1000)
    picture("threeslice", three)

    def iso_ux():
        ActivateDatabase(FL); iso("ux", 0.0005, 0.02, n=6, alpha=60); box()
        body(); DrawPlots(); goto(LAST)
        view((-0.6, -0.7, 0.35), focus=(0, 0, -0.4), scale=0.13); save("ch27-glyco-iso-ux", 1000, 1000)
    picture("isosurfaces of ux", iso_ux)

    def vec_slice():
        ActivateDatabase(FL)
        pseudo("vortmag", opacity=0.7); box(); slice_op("z", -0.42)
        vectors(n=3000); box(); slice_op("z", -0.42)
        body(); DrawPlots(); goto(LAST)
        view((0, 0, 1), up=(0, 1, 0), focus=(0, 0, -0.42), scale=0.07); save("ch27-glyco-vectors-slice", 1000, 1000)
    picture("vectors on a slice", vec_slice)

    def stream():
        # (VisIt 3.5: a Pseudocolor of "operators/IntegralCurve/U" fails beside a second database; the operator on U works)
        ActivateDatabase(FL); AddPlot("Pseudocolor", "U"); AddOperator("IntegralCurve")
        ic = IntegralCurveAttributes()
        ic.sourceType = ic.SpecifiedLine; ic.lineStart = (-0.06, -0.05, -0.42); ic.lineEnd = (-0.06, 0.05, -0.42)
        ic.sampleDensity0 = 21; ic.dataValue = ic.Speed; ic.integrationDirection = ic.Forward
        ic.maxSteps = 5000; ic.terminateByDistance = 1; ic.termDistance = 0.12; ic.maxStepLength = 0.002
        ic.issueAdvectionWarnings = 0; ic.issueBoundaryWarnings = 0; ic.issueTerminationWarnings = 0
        ic.issueStepsizeWarnings = 0; ic.issueStiffnessWarnings = 0; ic.issueCriticalPointsWarnings = 0
        SetOperatorOptions(ic)
        p = PseudocolorAttributes(); p.colorTableName = "viridis"; p.lineWidth = 2; SetPlotOptions(p)
        body(); DrawPlots(); goto(LAST)
        view((-0.3, -0.5, 0.8), focus=(0, 0, -0.42), scale=0.09); save("ch27-glyco-streamlines", 1000, 1000)
    picture("streamlines", stream)

P("done")
sys.exit(0)
