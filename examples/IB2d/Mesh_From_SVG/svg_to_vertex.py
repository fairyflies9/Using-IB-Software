"""svg_to_vertex.py: Lagrangian points at a fixed spacing from the paths of an SVG file (chapter 4f of Using IB Software).

    python3 svg_to_vertex.py drawing.svg [--input2d input2d] [--fit uniform|stretch] [--size S] [--center X,Y]
                             [--name NAME] [--spacing DS] [--merge-tol T] [--mode chord|arc] [--plot]

What it does, in the order MeshmerizeMe does it (Senter et al. 2021; Senter's Bezier notes):
  1. read every <path> (and <line>, <polyline>, <polygon>, <rect> without rounded corners, <circle>, <ellipse>) of the
     SVG; parse the path data (M L H V C S Q T A Z, absolute and relative, implicit repeats, compact numbers such as
     "-.7739.588586", arc flags written without separators);
  2. merge consecutive pieces whose start is the previous piece's end (ContourizeMe writes one tiny cubic per path):
     each contour becomes one poly-Bezier curve;
  3. map SVG coordinates (origin top left, y down) to the simulation box [0, Lx] x [0, Ly] (origin bottom left):
     --fit stretch maps the viewBox onto the whole box (each axis scaled separately, as the notes' map T does);
     --fit uniform (default) keeps the shape (one scale, the drawing centred); --size and --center then resize the
     drawing (its largest dimension) and move its centre, as the starfish example's MATLAB script does by hand;
  4. place points along each contour with EQUAL CHORDS (--mode chord, the default): neighbours a Euclidean distance
     ds = Lx/(2 Nx) apart, the condition MeshmerizeMe imposes (equation 1 of the paper), here met by walking along
     the finely sampled curve instead of by gradient descent; on a closed contour the chord is adjusted slightly
     (bisection) so that the closing chord matches too. --mode arc places points at equal ARC LENGTH instead, which
     on a wiggly traced outline leaves the chords shorter than ds;
  5. write NAME.vertex (count, then "x y" per line, 16 digits) and, with --plot, NAME_points.png.
Lx, Ly, Nx and string_name come from the input2d file (IB2d's format; only these keys are read).
Dependencies: NumPy; Matplotlib for --plot. GPL-3.0-compatible (BSD-3 in this repository).
"""
import math
import re
import sys
import xml.etree.ElementTree as ET
import numpy as np

_CMDS = "MmLlHhVvCcSsQqTtAaZz"
_NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")


# ---------------------------------------------------------------------------------------------- input2d
def read_input2d(path):
    keys = {}
    for line in open(path):
        s = line.split("%")[0].split("#")[0].strip()
        m = re.match(r"^(\w+)\s*=\s*(\S+)", s)
        if m:
            keys[m.group(1)] = m.group(2).strip('"')
    out = {"Lx": float(keys["Lx"]), "Ly": float(keys["Ly"]), "Nx": int(float(keys["Nx"]))}
    out["string_name"] = keys.get("string_name", "mesh")
    return out


# ---------------------------------------------------------------------------------------------- path data
def _tokens(d):
    """Split path data into (command, [args]) with arcs' one-character flags handled."""
    out = []
    for m in re.finditer(r"([%s])([^%s]*)" % (_CMDS, _CMDS), d):
        cmd, body = m.group(1), m.group(2)
        if cmd in "Aa":
            args, i = [], 0
            while i < len(body):
                k = len(args) % 7
                while i < len(body) and body[i] in " ,\t\r\n":
                    i += 1
                if i >= len(body):
                    break
                if k in (3, 4):                       # large-arc and sweep flags: a single 0 or 1
                    args.append(float(body[i])); i += 1
                else:
                    n = _NUM.match(body, i)
                    if not n:
                        raise ValueError("bad arc data near %r" % body[i:i + 20])
                    args.append(float(n.group(0))); i = n.end()
        else:
            args = [float(x) for x in _NUM.findall(body)]
        out.append((cmd, args))
    return out


def _arc_to_cubics(p0, rx, ry, phi_deg, fa, fs, p1):
    """SVG endpoint arc -> list of cubic segments (SVG 1.1 appendix F.6.5)."""
    x1, y1 = p0; x2, y2 = p1
    if x1 == x2 and y1 == y2:                         # SVG 1.1 F.6.2: an arc to its own start point is omitted
        return []
    if rx == 0 or ry == 0:                            # F.6.2: a zero radius makes it a straight line
        return [("L", np.array(p0), np.array(p1))]
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg); c, s = math.cos(phi), math.sin(phi)
    dx, dy = (x1 - x2) / 2, (y1 - y2) / 2
    x1p, y1p = c * dx + s * dy, -s * dx + c * dy
    lam = x1p ** 2 / rx ** 2 + y1p ** 2 / ry ** 2
    if lam > 1:
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx ** 2 * ry ** 2 - rx ** 2 * y1p ** 2 - ry ** 2 * x1p ** 2
    den = rx ** 2 * y1p ** 2 + ry ** 2 * x1p ** 2
    co = math.sqrt(max(0.0, num / den)) * (-1 if fa == fs else 1)
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    cx, cy = c * cxp - s * cyp + (x1 + x2) / 2, s * cxp + c * cyp + (y1 + y2) / 2

    def ang(u, v):
        a = math.atan2(u[0] * v[1] - u[1] * v[0], u[0] * v[0] + u[1] * v[1])
        return a
    t1 = ang((1, 0), ((x1p - cxp) / rx, (y1p - cyp) / ry))
    dt = ang(((x1p - cxp) / rx, (y1p - cyp) / ry), ((-x1p - cxp) / rx, (-y1p - cyp) / ry))
    if not fs and dt > 0:
        dt -= 2 * math.pi
    elif fs and dt < 0:
        dt += 2 * math.pi
    nseg = max(1, int(math.ceil(abs(dt) / (math.pi / 2))))
    segs, d = [], dt / nseg
    k = 4 / 3 * math.tan(d / 4)

    def pt(t):
        return np.array([cx + rx * math.cos(t) * c - ry * math.sin(t) * s, cy + rx * math.cos(t) * s + ry * math.sin(t) * c])

    def dpt(t):
        return np.array([-rx * math.sin(t) * c - ry * math.cos(t) * s, -rx * math.sin(t) * s + ry * math.cos(t) * c])
    for i in range(nseg):
        a, b = t1 + i * d, t1 + (i + 1) * d
        pa, pb = pt(a), pt(b)
        segs.append(("C", pa, pa + k * dpt(a), pb - k * dpt(b), pb))
    segs[0] = ("C", np.array(p0, float)) + segs[0][2:]
    segs[-1] = segs[-1][:4] + (np.array(p1, float),)
    return segs


def parse_path(d):
    """Path data -> list of (segments, closed); a segment is ('L', p0, p1), ('Q', p0, c, p1) or ('C', p0, c1, c2, p1)."""
    subpaths, segs, closed = [], [], False
    cur = np.zeros(2); start = np.zeros(2); last_c = None; last_cmd = ""
    for cmd, a in _tokens(d):
        rel = cmd.islower(); C = cmd.upper()
        if C == "Z":
            if np.linalg.norm(cur - start) > 0:
                segs.append(("L", cur.copy(), start.copy()))
            cur = start.copy(); closed = True; last_c = None; last_cmd = "Z"
            subpaths.append((segs, closed)); segs, closed = [], False
            continue
        size = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7}[C]
        if size and len(a) % size:
            raise ValueError("command %s has %d numbers" % (cmd, len(a)))
        for j in range(0, len(a), size):
            v = a[j:j + size]
            base = cur if rel else np.zeros(2)
            if C == "M":
                if segs:
                    subpaths.append((segs, closed)); segs, closed = [], False
                cur = base + v[:2]; start = cur.copy(); last_c = None
                C = "L"                               # implicit repeats after M are line-tos
                continue
            if C == "L":
                p = base + v[:2]; segs.append(("L", cur.copy(), p)); cur = p; last_c = None
            elif C == "H":
                p = np.array([(cur[0] if rel else 0) + v[0], cur[1]]); segs.append(("L", cur.copy(), p)); cur = p; last_c = None
            elif C == "V":
                p = np.array([cur[0], (cur[1] if rel else 0) + v[0]]); segs.append(("L", cur.copy(), p)); cur = p; last_c = None
            elif C == "C":
                c1, c2, p = base + v[0:2], base + v[2:4], base + v[4:6]
                segs.append(("C", cur.copy(), c1, c2, p)); last_c = ("C", c2); cur = p
            elif C == "S":
                c1 = 2 * cur - last_c[1] if last_c and last_c[0] == "C" else cur.copy()
                c2, p = base + v[0:2], base + v[2:4]
                segs.append(("C", cur.copy(), c1, c2, p)); last_c = ("C", c2); cur = p
            elif C == "Q":
                c1, p = base + v[0:2], base + v[2:4]
                segs.append(("Q", cur.copy(), c1, p)); last_c = ("Q", c1); cur = p
            elif C == "T":
                c1 = 2 * cur - last_c[1] if last_c and last_c[0] == "Q" else cur.copy()
                p = base + v[0:2]
                segs.append(("Q", cur.copy(), c1, p)); last_c = ("Q", c1); cur = p
            elif C == "A":
                p = base + v[5:7]
                segs.extend(_arc_to_cubics(cur.copy(), v[0], v[1], v[2], int(v[3]), int(v[4]), p)); cur = p; last_c = None
        last_cmd = C
    if segs:
        subpaths.append((segs, closed))
    return subpaths


def _shape_paths(el, tag):
    """The basic shapes as path data (rounded rectangles are refused, as in MeshmerizeMe's notes)."""
    g = lambda k, dflt=0.0: float(el.get(k, dflt))
    if tag == "line":
        return "M%r %r L%r %r" % (g("x1"), g("y1"), g("x2"), g("y2"))
    if tag in ("polyline", "polygon"):
        nums = _NUM.findall(el.get("points", ""))
        d = "M" + " ".join(nums[:2]) + " L" + " ".join(nums[2:])
        return d + (" Z" if tag == "polygon" else "")
    if tag == "rect":
        if g("rx") or g("ry"):
            raise ValueError("rounded rectangles are not supported; convert them to paths")
        x, y, w, h = g("x"), g("y"), g("width"), g("height")
        return "M%r %r h%r v%r h%r Z" % (x, y, w, h, -w)
    if tag in ("circle", "ellipse"):
        cx, cy = g("cx"), g("cy")
        rx = g("r") if tag == "circle" else g("rx"); ry = g("r") if tag == "circle" else g("ry")
        return "M%r %r A%r %r 0 1 0 %r %r A%r %r 0 1 0 %r %r Z" % (cx - rx, cy, rx, ry, cx + rx, cy, rx, ry, cx - rx, cy)
    return None


def read_svg(path):
    root = ET.parse(path).getroot()
    if any(el.get("transform") for el in root.iter()):
        print("warning: the SVG uses transform attributes, which this script ignores; flatten them first "
              "(e.g. Inkscape: Path > Object to Path, then save as plain or optimised SVG)", file=sys.stderr)
    vb = root.get("viewBox")
    if vb:
        minx, miny, w, h = [float(x) for x in _NUM.findall(vb)]
    else:
        minx, miny = 0.0, 0.0
        w = float(_NUM.findall(root.get("width"))[0]); h = float(_NUM.findall(root.get("height"))[0])
    pieces = []
    skip = {"defs", "clipPath", "mask", "symbol", "marker", "pattern", "metadata", "title", "desc"}

    def hidden(el):
        return el.get("display") == "none" or "display:none" in (el.get("style") or "").replace(" ", "")

    def walk(el):                                     # only what is drawn: not inside <defs>, <clipPath>, ...
        tag = el.tag.split("}")[-1]
        if tag in skip or hidden(el):
            return
        d = el.get("d") if tag == "path" else _shape_paths(el, tag)
        if d:
            pieces.extend(parse_path(d))
        for ch in el:
            walk(ch)
    walk(root)
    return pieces, (minx, miny, w, h)


# ---------------------------------------------------------------------------------------------- geometry
def _eval(seg, t):
    t = t[:, None]
    if seg[0] == "L":
        return (1 - t) * seg[1] + t * seg[2]
    if seg[0] == "Q":
        return (1 - t) ** 2 * seg[1] + 2 * (1 - t) * t * seg[2] + t ** 2 * seg[3]
    return (1 - t) ** 3 * seg[1] + 3 * (1 - t) ** 2 * t * seg[2] + 3 * (1 - t) * t ** 2 * seg[3] + t ** 3 * seg[4]


def merge_pieces(pieces, tol):
    """Join consecutive pieces whose start is the previous end (within tol, in SVG units)."""
    contours = []
    for segs, closed in pieces:
        if not segs:
            continue
        if contours and not contours[-1][1] and not closed and np.linalg.norm(contours[-1][0][-1][-1] - segs[0][1]) <= tol:
            contours[-1][0].extend(segs)
        else:
            contours.append([list(segs), closed])
    for c in contours:                                    # a merged chain that returns to its start is closed
        if not c[1] and np.linalg.norm(c[0][-1][-1] - c[0][0][1]) <= tol:
            c[1] = True
    return contours


def polyline(segs, per_seg=48):
    pts = [segs[0][1][None, :]]
    t = np.linspace(0, 1, per_seg + 1)[1:]
    for s in segs:
        pts.append(_eval(s, t))
    return np.vstack(pts)


def resample(P, ds, closed):
    """Points at equal arc length along the polyline P, spacing as close to ds as a whole number of intervals allows."""
    if closed and np.linalg.norm(P[-1] - P[0]) > 0:
        P = np.vstack([P, P[:1]])
    seg = np.hypot(*np.diff(P, axis=0).T); s = np.r_[0, np.cumsum(seg)]; L = s[-1]
    m = max(1, int(round(L / ds)))
    sk = np.linspace(0, L, m + 1)
    if closed:
        sk = sk[:-1]
    x = np.interp(sk, s, P[:, 0]); y = np.interp(sk, s, P[:, 1])
    return np.c_[x, y], L


def _walk_chords(P, h):
    """Greedy walk along the polyline P: each new point is the first point of P's path at Euclidean distance h from
    the previous one (the circle |x - q| = h intersected with the segment that crosses it)."""
    out = [P[0]]; q = P[0]; i = 0; n = len(P)
    while True:
        j = i + 1
        while j < n and np.linalg.norm(P[j] - q) < h:
            j += 1
        if j >= n:
            break
        a, b = P[j - 1], P[j]; d = b - a; f = a - q
        A, B, C = d @ d, 2 * f @ d, f @ f - h * h
        disc = max(B * B - 4 * A * C, 0.0)
        s = (-B + np.sqrt(disc)) / (2 * A) if A > 0 else 0.0
        q = a + min(max(s, 0.0), 1.0) * d
        out.append(q); i = j - 1
        P = P.copy(); P[i] = q                      # continue from the new point on that segment
    return np.array(out)


FALLBACKS = 0


def resample_chords(P, ds, closed):
    """Points with EQUAL CHORDS (the distance MeshmerizeMe controls, equation (1) of Senter et al.). A walk from the
    contour's first point places points a chord h apart; f(h) = (points walked - 1) + (gap to the end)/h counts the
    chords, continuously, and decreases with h. The chord count n = round(f(ds)) is kept and h is found by bisection
    so that f(h) = n: every chord, including the last one (to the end of an open contour, or back to the start of a
    closed one), is h, within a fraction 1/(2n) of ds. Open contours keep both end points."""
    if closed and np.linalg.norm(P[-1] - P[0]) > 0:
        P = np.vstack([P, P[:1]])
    L = np.sum(np.hypot(*np.diff(P, axis=0).T))
    E = P[-1]

    def f(h):
        Q = _walk_chords(P, h)
        return (len(Q) - 1) + np.linalg.norm(Q[-1] - E) / h, Q
    f0, _ = f(ds)
    n = max(1, int(round(f0)))
    if n == 1:
        return (np.vstack([P[0], E]) if not closed else P[:1].copy()), L
    lo, hi = 0.5 * ds, 2.0 * ds                       # f(lo) > n > f(hi) for any reasonable contour
    for _ in range(60):
        h = 0.5 * (lo + hi); fh, Q = f(h)
        if fh > n:
            lo = h
        else:
            hi = h
    h = 0.5 * (lo + hi); fh, Q = f(h)
    Q = Q[:n]
    if not closed:
        Q = np.vstack([Q, E])
    last = np.linalg.norm((Q[-1] if not closed else Q[0]) - (Q[-2] if not closed else Q[-1]))
    if not (0.8 * h <= last <= 1.25 * h):          # f(h) jumped over n (a hook or near-contact): use equal arc length
        global FALLBACKS
        FALLBACKS += 1
        return resample(P[:-1] if closed else P, ds, closed)
    return Q, L


def resample_chords_robust(P, ds, closed):
    """resample_chords, retried from up to 11 other starting points on a closed contour if the first try falls back."""
    global FALLBACKS
    before = FALLBACKS
    Q, L = resample_chords(P, ds, closed)
    if not closed or FALLBACKS == before:
        return Q, L
    base = P[:-1] if np.linalg.norm(P[-1] - P[0]) == 0 else P
    for k in range(1, 12):
        FALLBACKS = before
        Q2, L2 = resample_chords(np.roll(base, -k * len(base) // 12, axis=0), ds, closed)
        if FALLBACKS == before:
            return Q2, L2
    FALLBACKS = before + 1
    return Q, L


def svg_to_points(svg, Lx, Ly, Nx, fit="uniform", size=None, center=None, ds=None, merge_tol=None, per_seg=48, mode="chord"):
    pieces, (minx, miny, w, h) = read_svg(svg)
    # 1e-5 of the drawing joins pieces whose ends an optimiser (SVGO: three decimals) has rounded apart; 1e-6 did not
    # (IB2d's cropped_wing_opt.svg fell into 240 open pieces instead of 34 contours)
    tol = merge_tol if merge_tol is not None else 1e-5 * max(w, h)
    contours = merge_pieces(pieces, tol)
    ends = [(c[0][0][1], c[0][-1][-1]) for c in contours if not c[1]]
    near = sum(1 for i in range(len(ends)) for j in range(len(ends)) if i != j
               and np.linalg.norm(ends[i][1] - ends[j][0]) <= 0.01 * max(w, h))
    if near:
        print("hint: %d open contour ends lie within 1 %% of the drawing's size of another contour's start; if they "
              "should join, give a larger --merge-tol (in SVG units)" % near, file=sys.stderr)
    # SVG (y down) -> box (y up)
    if fit == "stretch":
        sx, sy, ox, oy = Lx / w, Ly / h, 0.0, 0.0
    else:
        sx = sy = min(Lx / w, Ly / h); ox, oy = (Lx - w * sx) / 2, (Ly - h * sy) / 2
    def T(P):
        return np.c_[(P[:, 0] - minx) * sx + ox, (miny + h - P[:, 1]) * sy + oy]
    polys = [(T(polyline(segs, per_seg)), closed) for segs, closed in contours]
    if size is not None or center is not None:
        allp = np.vstack([p for p, _ in polys]); lo, hi = allp.min(0), allp.max(0)
        f = size / max(hi - lo) if size is not None else 1.0
        c0 = (lo + hi) / 2; c1 = np.array(center) if center is not None else c0
        polys = [((p - c0) * f + c1, closed) for p, closed in polys]
    ds = ds if ds is not None else Lx / (2 * Nx)
    out, info = [], []
    for p, closed in polys:
        q, L = (resample_chords_robust if mode == "chord" else resample)(p, ds, closed)
        out.append(q); info.append((len(q), L, closed))
    return out, info, ds, len(pieces)


def write_vertex(name, contours):
    P = np.vstack(contours)
    with open(name + ".vertex", "w", newline="\n") as f:
        f.write("%d\n" % len(P))
        for x, y in P:
            f.write("%1.16e %1.16e\n" % (x, y))
    return P


if __name__ == "__main__":
    argv = sys.argv[1:]
    def opt(k, default=None, conv=str):
        if k in argv:
            i = argv.index(k); v = argv[i + 1]; del argv[i:i + 2]; return conv(v)
        return default
    inp = opt("--input2d", "input2d"); fit = opt("--fit", "uniform"); size = opt("--size", None, float)
    center = opt("--center", None, lambda s: [float(x) for x in s.split(",")]); name = opt("--name")
    ds = opt("--spacing", None, float); tol = opt("--merge-tol", None, float); mode = opt("--mode", "chord")
    plot = "--plot" in argv; argv = [a for a in argv if a != "--plot"]
    svg = argv[0]
    p = read_input2d(inp)
    contours, info, ds, npieces = svg_to_points(svg, p["Lx"], p["Ly"], p["Nx"], fit, size, center, ds, tol, mode=mode)
    name = name or p["string_name"]
    P = write_vertex(name, contours)
    print("%s: %d path pieces -> %d contours; ds = %.6g (Lx/(2 Nx) with Lx = %g, Nx = %d)" % (svg, npieces, len(info), ds, p["Lx"], p["Nx"]))
    for k, (n, L, closed) in enumerate(info):
        print("  contour %d: length %.6g, %d points, %s" % (k, L, n, "closed" if closed else "open"))
    d = np.concatenate([np.hypot(*np.diff(c if not cl else np.vstack([c, c[:1]]), axis=0).T) for c, (n, L, cl) in zip(contours, info) if len(c) > 1])
    print("wrote %s.vertex: %d points; spacing / ds: min %.4f median %.4f max %.4f%s" % (name, len(P), d.min() / ds, np.median(d) / ds, d.max() / ds,
          "; %d contour(s) used equal arc length (the equal-chord walk could not close evenly)" % FALLBACKS if FALLBACKS else ""))
    if plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 6 * p["Ly"] / p["Lx"] + 0.5))
        for c in contours:
            ax.plot(c[:, 0], c[:, 1], ".", ms=1.5)
        ax.set_xlim(0, p["Lx"]); ax.set_ylim(0, p["Ly"]); ax.set_aspect("equal"); ax.set_title("%s: %d points, ds = %.3g" % (name, len(P), ds))
        fig.tight_layout(); fig.savefig(name + "_points.png", dpi=150)
