"""sweep.py: the runs of the stability and convergence lab (chapter 4d of Using IB Software).

    python3 sweep.py GROUP [GROUP ...] [--redo] [--jobs N]

Groups (each case is a folder runs/<name>/ with its own input2d, band files and a copy of main2d.py):

  base    the shipped example as it is: 32 x 32, dt = 1e-3, k = 2.5e4, T = 1.5
  blowup  the two blow-ups of the course's lab: dt = 1 (T = 100), and a band 1000 times stiffer
  map     stiffness k = 2.5e3 ... 2.5e7 against dt = 4e-3 ... 1.25e-4 on 32 x 32, T = 0.3: which runs survive
  grid    16, 32, 64, 128, 256 with k scaled with Nx (same tension) and dt scaled with dx, T = 1.0; plus 64 x 64
          with the 32-grid's k (a softer band: the naive refinement)
  dt      64 x 64 at dt = 1e-3, 5e-4, 2.5e-4, 1.25e-4, T = 1.0
  map2    the map's edges: smaller dt for the stiff bands, larger dt for the soft ones
  grid2   16 ... 256 with k scaled with N^2 (the band the fluid feels is the same one; see the comment in the code)
  dt2     64 x 64 with the grid2 stiffness (1e5) at the four time steps
  grid3   16 ... 256 with TWO points per cell (ppc = 4) and k = 4 x grid2's (a band 2 x too tense: see grid4)
  grid4   16 ... 256 with two points per cell and k = 2 x grid2's: the same band as grid2 with twice the points
  all     all of the above

Dumps are written every 0.02 time units whatever dt is, so runs can be compared dump by dump. Each case records its
wall time, exit status, the last line of a failure and the number of dumps written in runs/summary.json, and
analyze.py turns its dumps into series.csv. A case that already has a summary entry is skipped unless --redo.
Run from this folder inside pyIB2d/Examples/ (the copied main2d.py looks for ../../../../IBM_Blackbox from runs/<name>/).
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from Rubberband import write_band          # noqa: E402
from analyze import series                 # noqa: E402

K32 = 2.5e4
DUMP_EVERY = 0.02


def case(name, Nx=32, dt=1e-3, T=1.5, k=None, timeout=4 * 3600, ppc=2):
    k = K32 * Nx / 32 if k is None else k
    return dict(name=name, Nx=Nx, dt=dt, T=T, k=k, ppc=ppc, print_dump=max(1, round(DUMP_EVERY / dt)), timeout=timeout)


GROUPS = {
    "base": [case("base32")],
    "blowup": [case("dt1_T100", dt=1.0, T=100.0, timeout=900), case("k1000x", k=K32 * 1000, T=0.1)],
    "map": [case("map_k%gx_dt%g" % (kf, dt), k=K32 * kf, dt=dt, T=0.3)
            for kf in (0.1, 1, 10, 100, 1000) for dt in (4e-3, 2e-3, 1e-3, 5e-4, 2.5e-4, 1.25e-4)],
    "grid": [case("grid%d" % N, Nx=N, dt=1e-3 * 32 / N, T=1.0) for N in (16, 32, 64, 128, 256)]
            + [case("grid64_samek", Nx=64, dt=5e-4, T=1.0, k=K32)],
    "dt": [case("dt64_%g" % dt, Nx=64, dt=dt, T=1.0) for dt in (1e-3, 5e-4, 2.5e-4, 1.25e-4)],
    # the map's edges: smaller dt for the stiff bands, larger dt for the soft ones
    "map2": [case("map_k%gx_dt%g" % (kf, dt), k=K32 * kf, dt=dt, T=0.3) for kf, dt in
             ((100, 6.25e-5), (100, 3.125e-5), (100, 1.5625e-5), (1000, 1.5625e-5), (10, 3e-3), (1, 8e-3), (1, 1.6e-2),
              (0.1, 8e-3), (0.1, 1.6e-2), (0.1, 3.2e-2), (0.1, 6.4e-2))],
}
# k scaled with N^2: IB2d spreads each point's force times ds (a force density per unit length), and the force itself is
# k times a spring length of order ds, so the fluid feels k ds^2 per link; keeping that fixed is k = 2.5e4 (N/32)^2.
# The "grid" group above scales k with N only and is kept as the wrong refinement (the band gets softer).
GROUPS["grid2"] = [case("gridq%d" % N, Nx=N, dt=1e-3 * 32 / N / (2 if N >= 256 else 1), T=1.0, k=K32 * (N / 32) ** 2)
                   for N in (16, 32, 64, 128, 256)]
GROUPS["dt2"] = [case("dtq64_%g" % dt, Nx=64, dt=dt, T=1.0, k=K32 * 4) for dt in (1e-3, 5e-4, 2.5e-4, 1.25e-4)]
# two points per cell (ppc = 4: ds = 0.48 dx), the same band (k scaled with 1/ds^2, so 4 x the grid2 value)
GROUPS["grid3"] = [case("gridp%d" % N, Nx=N, dt=5e-4 * 32 / N, T=1.0, k=K32 * 4 * (N / 32) ** 2, ppc=4)
                   for N in (16, 32, 64, 128, 256)]
# the driver spreads with ds = Lx/(2 Nx) whatever the actual spacing (two points per cell assumed), so with twice the points
# at the same grid the band needs k x 2, not x 4, to be the same band: grid3 above is the x 4 mistake (a band 1.4 x faster)
GROUPS["grid4"] = [case("gridr%d" % N, Nx=N, dt=5e-4 * 32 / N, T=1.0, k=K32 * 2 * (N / 32) ** 2, ppc=4)
                   for N in (16, 32, 64, 128, 256)]
GROUPS["all"] = sum((GROUPS[g] for g in ("base", "blowup", "map", "map2", "grid", "dt", "grid2", "dt2", "grid3", "grid4")), [])


def write_input2d(c, rundir):
    s = open(os.path.join(HERE, "input2d")).read()
    for key, val in (("Nx", "%d" % c["Nx"]), ("Ny", "%d" % c["Nx"]), ("dt", "%g" % c["dt"]),
                     ("Tfinal", "%g" % c["T"]), ("print_dump", "%d" % c["print_dump"]), ("plot_Matlab", "0")):
        s, n = re.subn(r"(?m)^%s\s*=\s*\S+" % key, "%s = %s" % (key, val), s)
        assert n == 1, key
    open(os.path.join(rundir, "input2d"), "w", newline="\n").write(s)


def run_case(c, redo=False):
    rundir = os.path.join(HERE, "runs", c["name"])
    done = os.path.join(rundir, "case.json")
    if os.path.exists(done) and not redo:
        return json.load(open(done))
    if os.path.exists(rundir):
        shutil.rmtree(rundir)
    os.makedirs(rundir)
    write_input2d(c, rundir)
    N, ds, dx = write_band(c["Nx"], c["k"], 0.0, outdir=rundir, ppc=c["ppc"])
    main = open(os.path.join(HERE, "main2d.py")).read().replace("'../../IBM_Blackbox'", "'../../../../IBM_Blackbox'")
    open(os.path.join(rundir, "main2d.py"), "w", newline="\n").write(main)
    t0 = time.time()
    status, last = "ok", ""
    with open(os.path.join(rundir, "run.log"), "w") as log:
        try:
            p = subprocess.run([sys.executable, "main2d.py"], cwd=rundir, stdout=log, stderr=subprocess.STDOUT,
                               timeout=c["timeout"], env=dict(os.environ, MPLBACKEND="Agg"))
            if p.returncode != 0:
                status = "failed"
        except subprocess.TimeoutExpired:
            status = "timeout"
    wall = time.time() - t0
    if status != "ok":
        lines = [l.rstrip() for l in open(os.path.join(rundir, "run.log"), errors="replace") if l.strip()]
        last = lines[-1] if lines else ""
    rows = series(rundir, c["dt"], c["print_dump"])
    res = dict(c, N=N, ds=ds, dx=dx, tension=c["k"] * ds, status=status, wall=wall, last=last,
               ndumps=len(rows), t_last=rows[-1][0] if rows else None,
               final=dict(zip(("t", "cx", "cy", "rx", "ry", "rmean", "perimeter", "area"), rows[-1])) if rows else None)
    json.dump(res, open(done, "w"), indent=1)
    print("%-22s %-7s %7.1f s  %4d dumps  %s" % (c["name"], status, wall, len(rows), last[:70]), flush=True)
    return res


if __name__ == "__main__":
    argv = sys.argv[1:]
    redo = "--redo" in argv
    jobs = 1
    if "--jobs" in argv:
        i = argv.index("--jobs"); jobs = int(argv[i + 1]); del argv[i:i + 2]
    args = [a for a in argv if not a.startswith("--")]
    cases = []
    for g in args or ["base"]:
        cases += [c for c in GROUPS[g] if c["name"] not in [x["name"] for x in cases]]
    os.makedirs(os.path.join(HERE, "runs"), exist_ok=True)
    with ThreadPoolExecutor(max_workers=jobs) as ex:
        results = list(ex.map(lambda c: run_case(c, redo), cases))
    summ = os.path.join(HERE, "runs", "summary.json")
    allres = json.load(open(summ)) if os.path.exists(summ) else {}
    for r in results:
        allres[r["name"]] = r
    json.dump(allres, open(summ, "w"), indent=1)
    print("%d cases in runs/summary.json" % len(allres))
