"""samrai_dumps.py: read IBAMR's VisIt dumps (SAMRAI HDF5 files) straight into NumPy, and put them on a uniform grid.

An IBAMR run writes, at every visualization dump, a folder viz_IB2d/visit_dump.NNNNN/ holding
    summary.samrai                   the patch hierarchy: levels, patches, extents, variable names, time
    processor_cluster.CCCCC.samrai   the field data, one file per MPI rank: processor.P/level.L/patch.N/<var>
and lists the folders in viz_IB2d/dumps.visit. VisIt reads them through its SAMRAI plugin; this module reads
them with h5py, which is what you want when the analysis is not a picture (averages, fluxes, time series, your
own plots). Requires numpy and h5py (pip install h5py, or apt install python3-h5py). Used by chapter 33 of
"Using IB Software".

    import samrai_dumps as sd
    d = sd.Dump("viz_IB2d/visit_dump.00341")          # one frame
    d.time, d.variables, d.levels                     # 0.01705, ['U', 'P', 'Omega', 'Div U'], 2
    x, y, omega = d.uniform("Omega")                  # on the finest level's grid: x (Nx+1,), y (Ny+1,), omega (Ny+1, Nx+1)
    x, y, (u, v) = d.uniform("U")                     # a vector: one array per component
    for step, t, folder in sd.frames("viz_IB2d"):     # the whole series from dumps.visit
        ...

Conventions: arrays are indexed [y, x] (row = y) like matplotlib's pcolormesh and MATLAB's meshgrid; nodal
variables (U, P, Omega in IBAMR 0.19) come back on the nodes of the fine grid, cell-centred ones (Div U) on the
cell centres; where a fine patch exists its values are used, elsewhere the coarse patch's values are
interpolated (nodal: bilinear; cell: repeated). The patch data inside the files are stored x-fastest.
"""
import os
import re
import sys

import numpy as np

try:
    import h5py
except ImportError:  # pragma: no cover
    h5py = None


class Dump:
    """One visualization dump (one visit_dump.NNNNN folder)."""

    def __init__(self, folder):
        if h5py is None:
            raise ImportError("samrai_dumps needs h5py (pip install h5py)")
        self.folder = folder
        with h5py.File(os.path.join(folder, "summary.samrai"), "r") as f:
            b = f["BASIC_INFO"]
            self.ndim = int(b["number_dimensions_of_problem"][0])
            self.variables = [v.decode() for v in b["var_names"][()]]
            self.cell_centered = {v: bool(c) for v, c in zip(self.variables, b["var_cell_centered"][()])}
            self.components = {v: int(c) for v, c in zip(self.variables, b["var_number_components"][()])}
            self.levels = int(b["number_levels"][0])
            self.patches_per_level = [int(n) for n in b["number_patches_at_level"][()]]
            self.dx = np.array(b["dx"][()])[:, : self.ndim]            # (levels, ndim)
            self.xlo = np.array(b["XLO"][()])[: self.ndim]
            self.ratios = np.array(b["ratios_to_coarser_levels"][()])[:, : self.ndim]
            self.time = float(b["time"][0])
            self.step = int(b["time_step_number"][0])
            self.nprocs = int(b["number_processors"][0])
            ext = f["extents"]["patch_extents"][()]
            pmap = f["extents"]["patch_map"][()]
            self.patches = []
            for e, m in zip(ext, pmap):
                self.patches.append(dict(level=int(m["level_number"]), number=int(m["patch_number"]),
                                         proc=int(m["processor_number"]), cluster=int(m["file_cluster_number"]),
                                         lower=np.array(e["lower"][: self.ndim]), upper=np.array(e["upper"][: self.ndim]),
                                         xlo=np.array(e["xlo"][: self.ndim]), xup=np.array(e["xup"][: self.ndim])))
        # the domain in level-0 cells: the union of the level-0 patch boxes
        lv0 = [p for p in self.patches if p["level"] == 0]
        self.n0 = np.max([p["upper"] for p in lv0], axis=0) + 1          # cells per direction on level 0
        self.fine_ratio = np.ones(self.ndim, dtype=int)
        for lv in range(1, self.levels):
            self.fine_ratio *= self.ratios[lv]
        self.nfine = self.n0 * self.fine_ratio                             # cells per direction on the finest level
        self.dxfine = self.dx[self.levels - 1]
        self.xup = self.xlo + self.nfine * self.dxfine
        self._files = {}

    # ---- raw patch data -----------------------------------------------------------------------------------------
    def _file(self, cluster):
        if cluster not in self._files:
            self._files[cluster] = h5py.File(os.path.join(self.folder, "processor_cluster.%05d.samrai" % cluster), "r")
        return self._files[cluster]

    def _dataset_names(self, var):
        """The dataset names of a variable in the processor files: 'P' for a scalar, 'U.00', 'U.01' for a vector."""
        n = self.components[var]
        return [var] if n == 1 else ["%s.%02d" % (var, c) for c in range(n)]

    def patch_data(self, patch, var):
        """The arrays of one patch (a list, one per component), shaped [y, x] (or [z, y, x]); nodal arrays have
        one more entry per direction than the patch has cells."""
        f = self._file(patch["cluster"])
        g = f["processor.%05d/level.%05d/patch.%05d" % (patch["proc"], patch["level"], patch["number"])]
        ncell = patch["upper"] - patch["lower"] + 1
        shape = ncell if self.cell_centered[var] else ncell + 1
        out = []
        for name in self._dataset_names(var):
            a = np.array(g[name][()], dtype=float)
            out.append(a.reshape(shape[::-1]))     # stored x-fastest: reshape as (ny, nx) / (nz, ny, nx)
        return out

    def patch_extent_values(self, var):
        """(min, max) over the dump as the summary file records them, for a check against your own numbers."""
        with h5py.File(os.path.join(self.folder, "summary.samrai"), "r") as f:
            names = self._dataset_names(var)
            mins, maxs = [], []
            for name in names:
                e = f["extents"]["%s-Extents" % name][()]
                defined = e["data_is_defined"].astype(bool)
                mins.append(float(e["min"][defined].min())); maxs.append(float(e["max"][defined].max()))
            return mins, maxs

    # ---- a uniform grid -----------------------------------------------------------------------------------------
    def uniform(self, var, level=None):
        """The variable on the uniform grid of a level (default: the finest), the whole domain.

        Returns (x, y, data) in 2D or (x, y, z, data) in 3D; data is one array for a scalar, a tuple of arrays for a
        vector. Nodal data sit on the nodes (x has Nx+1 entries), cell data on the centres (x has Nx entries).
        Coarser patches fill where no finer patch exists: nodal by bilinear interpolation, cell by repetition."""
        if level is None:
            level = self.levels - 1
        ratio_to_level = np.ones(self.ndim, dtype=int)                    # from level 0 to 'level'
        for lv in range(1, level + 1):
            ratio_to_level *= self.ratios[lv]
        n = self.n0 * ratio_to_level
        dx = self.dx[level]
        cell = self.cell_centered[var]
        shape = tuple((n if cell else n + 1)[::-1])
        ncomp = self.components[var]
        data = [np.full(shape, np.nan) for _ in range(ncomp)]
        for lv in range(0, level + 1):                                     # coarse first, fine on top
            r = np.ones(self.ndim, dtype=int)                              # from level lv to 'level'
            for k in range(lv + 1, level + 1):
                r *= self.ratios[k]
            for p in self.patches:
                if p["level"] != lv:
                    continue
                lo = p["lower"] * r
                hi = (p["upper"] + 1) * r                                   # exclusive, in cells of 'level'
                arrays = self.patch_data(p, var)
                for c in range(ncomp):
                    a = arrays[c]
                    if cell:
                        fine = a
                        for axis in range(self.ndim):                       # repeat each coarse cell r times
                            fine = np.repeat(fine, r[::-1][axis], axis=axis)
                        sl = tuple(slice(lo[::-1][ax], hi[::-1][ax]) for ax in range(self.ndim))
                    else:
                        fine = _refine_nodal(a, r[::-1])
                        sl = tuple(slice(lo[::-1][ax], hi[::-1][ax] + 1) for ax in range(self.ndim))
                    data[c][sl] = fine
        axes = []
        for ax in range(self.ndim):
            if cell:
                axes.append(self.xlo[ax] + dx[ax] * (np.arange(n[ax]) + 0.5))
            else:
                axes.append(self.xlo[ax] + dx[ax] * np.arange(n[ax] + 1))
        out = data[0] if ncomp == 1 else tuple(data)
        return (*axes, out)

    def close(self):
        for f in self._files.values():
            f.close()
        self._files = {}


def _refine_nodal(a, r):
    """Linear interpolation of a nodal array a (shape (ny+1, nx+1) [, (nz+1, ...)]) onto r times finer nodes.
    r is per axis in array order."""
    out = a
    for axis in range(a.ndim):
        n = out.shape[axis]
        if n < 2 or r[axis] == 1:
            continue
        old = np.arange(n, dtype=float)
        new = np.arange((n - 1) * r[axis] + 1, dtype=float) / r[axis]
        out = np.apply_along_axis(lambda col: np.interp(new, old, col), axis, out)
    return out


def frames(viz_dir):
    """The dumps listed in <viz_dir>/dumps.visit as (step, time, folder), in order."""
    out = []
    with open(os.path.join(viz_dir, "dumps.visit")) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            folder = os.path.join(viz_dir, os.path.dirname(line))
            m = re.search(r"visit_dump\.(\d+)", line)
            step = int(m.group(1)) if m else -1
            with h5py.File(os.path.join(folder, "summary.samrai"), "r") as s:
                t = float(s["BASIC_INFO"]["time"][0])
            out.append((step, t, folder))
    return out


def line_flux(x, y, u, x0, y_lo, y_hi):
    """Flow rate across the vertical line x = x0 between y_lo and y_hi from a nodal u(y, x) field on a uniform grid
    (the 2020 lecture's 'volumetric flow rate across the end of the tube'): trapezoid rule in y after linear
    interpolation in x. In 2D the result is a flow rate per unit depth (m^2/s)."""
    i = np.searchsorted(x, x0)
    i = min(max(i, 1), len(x) - 1)
    w = (x0 - x[i - 1]) / (x[i] - x[i - 1])
    ucol = (1 - w) * u[:, i - 1] + w * u[:, i]
    m = (y >= y_lo) & (y <= y_hi)
    return float(np.trapz(ucol[m], y[m]))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    d = Dump(sys.argv[1])
    print("time %g step %d  levels %d  patches %s  finest cells %s  dx %s" % (d.time, d.step, d.levels, d.patches_per_level, d.nfine.tolist(), d.dxfine.tolist()))
    for v in d.variables:
        print("  %-6s %s  components %d  file extents %s" % (v, "cell" if d.cell_centered[v] else "nodal", d.components[v], d.patch_extent_values(v)))
    var = sys.argv[2] if len(sys.argv) > 2 else d.variables[0]
    res = d.uniform(var)
    data = res[-1]
    arrays = data if isinstance(data, tuple) else (data,)
    for c, a in enumerate(arrays):
        print("  %s[%d] on the uniform grid: shape %s, min %g max %g, NaN %d" % (var, c, a.shape, np.nanmin(a), np.nanmax(a), int(np.isnan(a).sum())))
    d.close()
