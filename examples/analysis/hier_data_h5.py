"""hier_data_h5.py: the Eulerian state dumps that IBAMR's own examples write (hier_data_IB2d/hier_data.NNNNN.samrai.PPPPP)
in NumPy, with h5py (chapter 33).

IBAMR's examples/IB/explicit/ex1 (the origin of this series' output_data) and the upstream IBFE and complex-fluids
examples write, every data_dump_interval steps, the patch hierarchy with the integrator's current velocity and
pressure through SAMRAI's HDF5 database: one file per MPI rank with the layout
    PatchHierarchy/level_LLLL/level_LLLL-patch_NNNN/<Variable##Context>/d_data[0|1]/d_array
where <Variable##Context> is e.g. "INSStaggeredHierarchyIntegrator::P##INSStaggeredHierarchyIntegrator::CURRENT"
(cell-centred, one array) or "...::U##...::CURRENT" (side-centred: d_data0 for the x faces, d_data1 for the y
faces), each with its index box d_box, ghost width d_ghosts and depth d_depth. These are the solver's own arrays
(double precision, with ghost cells), not the single-precision nodal copies of the VisIt dumps. This series'
examples do not write them (chapter 11), the upstream ones do.

    import hier_data_h5 as hd
    f = hd.HierData("hier_data_IB2d/hier_data.00033.samrai.00000")
    f.variables                                   # the <Variable##Context> names found
    for p in f.patches("INSStaggeredHierarchyIntegrator::P##INSStaggeredHierarchyIntegrator::CURRENT"):
        p["level"], p["lo"], p["hi"], p["data"]   # data without ghosts, shaped [y, x]
"""
import sys

import numpy as np

try:
    import h5py
except ImportError:  # pragma: no cover
    h5py = None


class HierData:
    def __init__(self, path):
        if h5py is None:
            raise ImportError("hier_data_h5 needs h5py")
        self.path = path
        self.f = h5py.File(path, "r")
        self.h = self.f["PatchHierarchy"]
        self.nlevels = int(self.h["d_number_levels"][0])
        self.variables = []
        for lv in range(self.nlevels):
            g = self.h["level_%04d" % lv]
            for name in g:
                if name.startswith("level_") and "patch" in name:
                    for var in g[name]:
                        if "##" in var and var not in self.variables:
                            self.variables.append(var)
            if self.variables:
                break

    @staticmethod
    def _box(rec):
        r = rec[0] if rec.shape else rec
        dim = int(r["dim"]); return np.array(r["lo"][:dim]), np.array(r["hi"][:dim])

    def patches(self, var):
        """Every patch's data for one variable: dicts with level, lo, hi (index box, inclusive), ghosts, and data
        (cell data: one array [y, x]; side data: a list of arrays, one per face direction) without ghost cells."""
        out = []
        for lv in range(self.nlevels):
            g = self.h["level_%04d" % lv]
            for name in sorted(n for n in g if n.startswith("level_") and "patch" in n):
                if var not in g[name]:
                    continue
                pv = g[name][var]
                lo, hi = self._box(pv["d_box"][()])
                ghosts = np.array(pv["d_ghosts"][()])
                depth = int(pv["d_depth"][0])
                dim = len(lo)
                arrays = []
                keys = sorted(k for k in pv if k.startswith("d_data"))
                for k in keys:
                    dd = pv[k]
                    glo, ghi = self._box(dd["d_box"][()])      # the array's own box (with ghosts; side data: +1 in its axis)
                    shape = (ghi - glo + 1)[::-1]
                    a = np.array(dd["d_array"][()]).reshape((depth,) + tuple(shape))
                    # strip the ghost cells: keep lo..hi (plus one face for side data in its own axis)
                    sl = []
                    for axis in range(dim):
                        ax = dim - 1 - axis                     # array axis -> space axis
                        start = lo[ax] - glo[ax]
                        extra = 1 if (k != "d_data" and int(k[len("d_data"):]) == ax) else 0
                        stop = start + (hi[ax] - lo[ax] + 1) + extra
                        sl.append(slice(start, stop))
                    a = a[(slice(None),) + tuple(sl)]
                    arrays.append(a[0] if depth == 1 else a)
                out.append(dict(level=lv, name=name, lo=lo, hi=hi, ghosts=ghosts, data=arrays[0] if keys == ["d_data"] else arrays))
        return out

    def close(self):
        self.f.close()


if __name__ == "__main__":
    p = sys.argv[1]
    f = HierData(p)
    print(p, "levels", f.nlevels, "variables:")
    for v in f.variables:
        ps = f.patches(v)
        shapes = [(q["level"], (q["data"].shape if hasattr(q["data"], "shape") else [a.shape for a in q["data"]])) for q in ps[:3]]
        allv = np.concatenate([np.ravel(q["data"]) if hasattr(q["data"], "shape") else np.concatenate([np.ravel(a) for a in q["data"]]) for q in ps])
        print("  %s: %d patches, first %s, min %g max %g" % (v, len(ps), shapes, allv.min(), allv.max()))
    f.close()
