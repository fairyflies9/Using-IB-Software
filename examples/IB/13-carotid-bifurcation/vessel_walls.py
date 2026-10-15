"""vessel_walls.py: builds target-point walls for a 2D vessel tree from a closed outline, for example IB/13.

The outline (a closed polyline in mm, one of the *-outline.csv files made by tools/carotid_outline.py or
tools/project_outline.py from a surface model) is cut where the vessels leave the region of interest; each cut
splits the loop, and the open arcs that remain are the walls. The two walls of each cut vessel are extended straight
along the vessel's axis to the box face on that side, half a point spacing inside it, so that the inflow and outflow
conditions can be set on the faces. Every point is a target point.

    python3 vessel_walls.py --case horse        # the horse carotid (default): trunk in on the left, branches out through the top and bottom faces
    python3 vessel_walls.py --case human        # the human bifurcation: common carotid in on the left, two branches out on the right
    python3 vessel_walls.py --case horse --fine 2   # twice the resolution (the Puma run): the coarse grid and the point spacing follow

Units: cm. The numbers the input file needs are printed and written to <case>_geometry.txt; the walls go to
<case>.vertex and <case>.target, a picture to <case>-walls.png.
"""
import argparse
import sys

import numpy as np

CASES = {
    # outline file, the cuts that remove the vessel ends ("x<270" removes every point with x < 270 mm, and so on),
    # the length of straight vessel kept ahead of the inlet cut and after the outlet cuts (in inlet diameters),
    # and the model's scale (mm -> cm = 0.1): both models are used at their own size
    # cut values may be relative to the outline's range: "x<max-120" is 120 mm inside the largest x
    "horse": dict(outline="horse-outline.csv", cuts=["x<max-120", "y>max-17", "y<min+18"], inlet=1.5, outlet=0.5, scale=0.1,
                  note="equine carotid: the common carotid (left) meets the vessel that runs up to the internal carotid and occipital artery and down to the external carotid"),
    "human": dict(outline="carotid2-outline.csv", cuts=["x<min+1.5", "x>max-6"], inlet=1.5, outlet=0.75, scale=0.1,
                  note="human carotid bifurcation (NIH 3D model): common carotid (left) to internal (with the bulb) and external carotids (right)"),
}
ap = argparse.ArgumentParser()
ap.add_argument("--case", default="horse", choices=sorted(CASES))
ap.add_argument("--fine", type=float, default=1.0, help="resolution factor: 1 = the laptop grid, 2 = twice as fine")
ap.add_argument("--dxc", type=float, default=0.125, help="coarse cell size (cm) at --fine 1; the fine level is 4 times finer")
ap.add_argument("--DT", type=float, default=1.0e-4, help="the time step of the input file (s); the target stiffness is sized for it")
ap.add_argument("--kappa", type=float, default=None, help="target stiffness per point; default 0.2*RHO*DX^2/DT^2 with RHO 1.05")
ap.add_argument("--kappa_spring", type=float, default=None, help="stiffness of the springs between neighbouring wall points; default a quarter of the target stiffness (half with a single layer)")
ap.add_argument("--layers", type=int, default=1, help="rows of points across the wall, one point spacing apart, from the lumen outward (1 = a single row, the shipped files; 5 = a wall two fine cells thick, joined by springs along, across and diagonally)")
ap.add_argument("--margin", type=float, default=0.6, help="clear space (cm) between the vessel and the walls of the box on the closed sides")
args = ap.parse_args()
C = CASES[args.case]

# --- the outline: the lumen is the largest closed loop that is not the outer wall (the smaller of two concentric loops)
loops, cur = [], []
for line in open(C["outline"]):
    line = line.strip()
    if not line:
        if len(cur) > 10:
            loops.append(np.array(cur))
        cur = []
    else:
        cur.append([float(v) for v in line.split(",")])
if len(cur) > 10:
    loops.append(np.array(cur))
def area(p):
    x, y = p[:, 0], p[:, 1]
    return 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
loops.sort(key=area, reverse=True)
if len(loops) >= 2 and area(loops[1]) > 0.5 * area(loops[0]):
    P = loops[1]      # two concentric loops (a wall with thickness): the inner one is the lumen
else:
    P = loops[0]
if np.allclose(P[0], P[-1], atol=1e-3):
    P = P[:-1]
P = P.copy()
if args.case == "human":
    P[:, 0] = -P[:, 0]   # the STL's common carotid is at large x; flip so the flow runs in +x
print("outline: %d points, area %.0f mm^2" % (len(P), area(P)))

# --- cuts ---------------------------------------------------------------------------------------------------------
def parse(cut):
    ax, op, val = cut[0], cut[1], cut[2:]
    a_ = {"x": 0, "y": 1}[ax]
    if val.startswith("max"):
        v = P[:, a_].max() + float(val[3:] or 0)
    elif val.startswith("min"):
        v = P[:, a_].min() + float(val[3:] or 0)
    else:
        v = float(val)
    return a_, op, v
print("outline range: x %.1f to %.1f, y %.1f to %.1f mm" % (P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()))
cuts = [parse(c) for c in C["cuts"]]
def outside(p):
    return any((p[a] < v) if op == "<" else (p[a] > v) for a, op, v in cuts)
def crossing(a, b):
    """The point where segment a-b crosses the first cut it crosses, and that cut."""
    best = None
    for a_, op, v in cuts:
        da, db = a[a_] - v, b[a_] - v
        if (da < 0) != (db < 0):
            w = da / (da - db)
            if best is None or w < best[0]:
                best = (w, a_, v)
    w, a_, v = best
    c = a + w * (b - a); c[a_] = v
    return c
n = len(P)
start = next(i for i in range(n) if outside(P[i]))      # begin the walk outside, so every arc is complete
arcs, cur = [], []
for k in range(n):
    a, b = P[(start + k) % n], P[(start + k + 1) % n]
    ia, ib = not outside(a), not outside(b)
    if ia:
        cur.append(a)
    if ia != ib:
        c = crossing(a, b)
        if ia:
            cur.append(c); arcs.append(np.array(cur)); cur = []
        else:
            cur = [c]
print("walls after the cuts: %d arcs with %s points" % (len(arcs), [len(a) for a in arcs]))

# --- scale, place, grid ---------------------------------------------------------------------------------------------
s = C["scale"]
arcs = [a * s for a in arcs]
ends = [(k, e) for k in range(len(arcs)) for e in (0, -1)]
# which face each end leaves through: the cut it lies on
def face_of(p):
    for a_, op, v in cuts:
        if abs(p[a_] - v * s) < 1e-6:
            return (a_, op)
    raise SystemExit("an arc end is not on a cut: %s" % p)
faces = {ke: face_of(arcs[ke[0]][ke[1]]) for ke in ends}
inlet_face = [f for f in set(faces.values()) if f == (0, "<")]
if not inlet_face:
    raise SystemExit("no inlet cut (the inlet must be an x< cut)")
# the inlet width sets the extension lengths
inlet_ends = sorted([ke for ke in ends if faces[ke] == (0, "<")], key=lambda ke: arcs[ke[0]][ke[1]][1])
D_in = abs(arcs[inlet_ends[0][0]][inlet_ends[0][1]][1] - arcs[inlet_ends[1][0]][inlet_ends[1][1]][1])
print("inlet width %.3f cm" % D_in)
allp = np.vstack(arcs)
lo = allp.min(0) - args.margin; hi = allp.max(0) + args.margin
for a_, op, v in cuts:
    ext = (C["inlet"] if (a_, op) == (0, "<") else C["outlet"]) * D_in
    if op == "<":
        lo[a_] = v * s - ext
    else:
        hi[a_] = v * s + ext
dxc = args.dxc / args.fine
NX, NY = int(np.ceil((hi[0] - lo[0]) / dxc)), int(np.ceil((hi[1] - lo[1]) / dxc))
NX += NX % 2; NY += NY % 2
LX, LY = NX * dxc, NY * dxc
# shift so that the box is [0, LX] x [0, LY] with the cut faces exactly on the box faces that carry them
shift = -lo
arcs = [a + shift for a in arcs]
DX = dxc / 4
ds = DX / 2
print("box %.3f x %.3f cm, coarse %d x %d cells of %.4f cm, fine cells %.5f cm, point spacing %.5f cm" % (LX, LY, NX, NY, dxc, DX, ds))

# --- extend the vessel ends to their faces -------------------------------------------------------------------------
def end_dir(a, end):
    pts = a if end == -1 else a[::-1]
    tail = pts[np.linalg.norm(pts - pts[-1], axis=1) < 4 * D_in / 7.0 * 0.4]   # the last ~0.4 mm-per-mm... about half a diameter
    if len(tail) < 2:
        tail = pts[-3:]
    d = pts[-1] - tail[0]
    return d / np.linalg.norm(d)
groups = {}
for ke in ends:
    groups.setdefault(faces[ke], []).append(ke)
bands = {}
for f, kes in groups.items():
    a_, op = f
    other = 1 - a_
    kes = sorted(kes, key=lambda ke: arcs[ke[0]][ke[1]][other])
    if len(kes) % 2:
        raise SystemExit("an odd number of wall ends on a face: %s" % [arcs[k][e] for k, e in kes])
    for i in range(0, len(kes), 2):
        pair = kes[i:i + 2]
        d = sum(end_dir(arcs[k], e) for k, e in pair); d /= np.linalg.norm(d)
        target = (0.5 * ds) if op == "<" else ([LX, LY][a_] - 0.5 * ds)
        for k, e in pair:
            p = arcs[k][e]
            t = (target - p[a_]) / d[a_]
            q = p + t * d
            arcs[k] = np.vstack([arcs[k], [q]]) if e == -1 else np.vstack([[q], arcs[k]])
        ys = sorted(arcs[k][e][other] for k, e in pair)
        bands.setdefault(f, []).append(ys)
        print("vessel on face %s%s: axis (%.3f, %.3f), spans %.3f to %.3f cm, width %.3f" % ("xy"[a_], op, d[0], d[1], ys[0], ys[1], ys[1] - ys[0]))

# --- resample, nudge, write -----------------------------------------------------------------------------------------
def resample(a, ds):
    seg = np.linalg.norm(np.diff(a, axis=0), axis=1)
    sarc = np.concatenate([[0], np.cumsum(seg)])
    m = max(2, int(round(sarc[-1] / ds)) + 1)
    t = np.linspace(0, sarc[-1], m)
    return np.column_stack([np.interp(t, sarc, a[:, 0]), np.interp(t, sarc, a[:, 1])]), sarc[-1]
# The wall is LAYERS rows of points: the lumen row, then rows one spacing further out along the wall's outward
# normal (away from the lumen), so that the wall is a band LAYERS*ds thick with springs along, across and
# diagonally between the rows: a connected elastic sheet rather than a single leaky row.
ccw = (0.5 * (np.dot(P[:, 0], np.roll(P[:, 1], -1)) - np.dot(P[:, 1], np.roll(P[:, 0], -1)))) > 0   # loop orientation
walls, rows_of = [], []
for k, a in enumerate(arcs):
    r, L = resample(a, ds)
    t = np.gradient(r, axis=0); t /= np.linalg.norm(t, axis=1)[:, None]
    nrm = np.column_stack([t[:, 1], -t[:, 0]]) if ccw else np.column_stack([-t[:, 1], t[:, 0]])   # outward for the walk's direction
    rows = [r + j * ds * nrm for j in range(args.layers)]
    walls.extend(rows); rows_of.append(rows)
    print("wall %d: %.2f cm, %d points per row, %d rows" % (k, L, len(r), args.layers))
# an outer row of a wall that meets a face at an angle runs past the face: those points are dropped (not clipped:
# clipping piled them up on the face and the horse case blew up there at t = 0.11 s), and the springs below skip them
ids_of = []     # per wall, per row: the global index of each point, or -1 where it was dropped
pts = []
for rows in rows_of:
    ids_rows = []
    for row in rows:
        ids = []
        for p in row:
            if 0.5 * ds <= p[0] <= LX - 0.5 * ds and 0.5 * ds <= p[1] <= LY - 0.5 * ds:
                ids.append(len(pts)); pts.append(p)
            else:
                ids.append(-1)
        ids_rows.append(ids)
    ids_of.append(ids_rows)
X = np.array(pts)
print("dropped %d outer-row points that fell outside the box" % (sum(len(r) for rows in rows_of for r in rows) - len(X)))
r = X / DX
on_face = np.abs(r - np.round(r)) < 1e-7
X[on_face] += 1e-3 * DX
RHO = 1.05
kappa = args.kappa if args.kappa is not None else 0.2 * RHO * DX ** 2 / args.DT ** 2
kappa_spring = args.kappa_spring if args.kappa_spring is not None else (0.25 if args.layers > 1 else 0.5) * kappa
name = args.case
with open(name + ".vertex", "w", newline="\n") as f:
    f.write("%d\n" % len(X))
    for x, y in X:
        f.write("%1.16e %1.16e\n" % (x, y))
with open(name + ".target", "w", newline="\n") as f:
    f.write("%d\n" % len(X))
    for i in range(len(X)):
        f.write("%d %1.16e\n" % (i, kappa))
# springs: along each row, across neighbouring rows, and on both diagonals between them (shear stiffness); never
# between different walls. Rest length = the distance as written.
springs = []
def link(i, j):
    if i >= 0 and j >= 0:
        springs.append((i, j, float(np.linalg.norm(X[j] - X[i]))))
for ids_rows in ids_of:
    n_r, n_l = len(ids_rows[0]), len(ids_rows)
    for j in range(n_l):
        for i in range(n_r - 1):
            link(ids_rows[j][i], ids_rows[j][i + 1])
        if j + 1 < n_l:
            for i in range(n_r):
                link(ids_rows[j][i], ids_rows[j + 1][i])
                if i + 1 < n_r:
                    link(ids_rows[j][i], ids_rows[j + 1][i + 1]); link(ids_rows[j][i + 1], ids_rows[j + 1][i])
with open(name + ".spring", "w", newline="\n") as f:
    f.write("%d\n" % len(springs))
    for i, j, L in springs:
        f.write("%d %d %1.16e %1.16e\n" % (i, j, kappa_spring, L))
print("springs: %d (along, across and diagonal), stiffness %.1f (targets %.1f); %d rows, wall %.3f cm thick; %.1f points per fine cell along the wall" % (len(springs), kappa_spring, kappa, args.layers, (args.layers - 1) * ds, DX / ds))
inlet = bands[(0, "<")][0]
geom = {"case": name, "LX": LX, "LY": LY, "NX": NX, "NY": NY, "DX_coarse": dxc, "DX": DX, "ds": ds, "D_inlet": D_in,
        "n_points": len(X), "n_springs": len(springs), "kappa_file": kappa, "kappa_spring": kappa_spring,
        "inlet_y_lo": inlet[0], "inlet_y_hi": inlet[1],
        "outlets": {("xy"[f[0]] + f[1]): b for f, b in bands.items() if f != (0, "<")}}
with open(name + "_geometry.txt", "w", newline="\n") as f:
    for k, v in geom.items():
        f.write("%s = %s\n" % (k, v)); print("%s = %s" % (k, v))
print("wrote %s.vertex, %s.target, %s_geometry.txt" % (name, name, name))
try:
    from PIL import Image, ImageDraw
    sc = max(60, int(1000 / max(LX, LY)))
    W, H = int(LX * sc), int(LY * sc)
    im = Image.new("RGB", (W + 1, H + 1), "white"); dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, W, H], outline="gray")
    for k, w in enumerate(walls):
        dr.line([(x * sc, H - y * sc) for x, y in w], fill=["black", "red", "blue", "green", "purple", "orange", "brown"][k % 7], width=2)
    dr.line([(2, H - inlet[0] * sc), (2, H - inlet[1] * sc)], fill="green", width=5)
    dr.text((5, 5), "IB/13 %s: %d target points, ds = %.4f cm, inlet %.2f cm wide (green); box %.1f x %.1f cm" % (name, len(X), ds, D_in, LX, LY), fill="black")
    im.save(name + "-walls.png"); print("wrote %s-walls.png" % name)
except ImportError:
    pass
