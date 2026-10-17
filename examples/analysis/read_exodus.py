"""read_exodus.py: the ExodusII file of an IBFE run (viz_IB2d/output.ex2) in NumPy, through netCDF4 (chapter 33).

ExodusII is a netCDF file with a fixed vocabulary (dimensions num_nodes, num_elem, time_step; variables coordx,
coordy[, coordz], connect<b> per element block, time_whole, name_nod_var and vals_nod_var<k>). IBAMR's IBFE writes
the reference mesh once and, at every visualization dump, the nodal fields X_0.., dX_0.., U_0.., F_0.. (chapter 28).
Requires numpy and netCDF4 (pip install netCDF4, or apt install python3-netcdf4); h5py also opens these files
(they are netCDF-4/HDF5) but netCDF4 gives the names.

    import read_exodus as rx
    m = rx.Exodus("viz_IB2d/output.ex2")
    m.times                        # (41,) the dump times
    m.coords                       # (num_nodes, 2 or 3) the reference positions
    m.connect["1"]                 # (num_elem, nodes per element) 0-based connectivity of block 1
    m.var("dX_1", state=10)        # (num_nodes,) one field at one state (0-based: state 10 = the 11th dump)
    m.var("dX_1")                  # (num_states, num_nodes) the whole history
    m.positions(10)                # coords + dX at state 10: the current configuration
"""
import sys

import numpy as np

try:
    from netCDF4 import Dataset
except ImportError:  # pragma: no cover
    Dataset = None


def _names(var):
    """Exodus stores names as fixed-width char arrays."""
    out = []
    for row in var[:]:
        if hasattr(row, "tobytes"):
            s = row.tobytes().decode("ascii", "ignore")
        else:
            s = b"".join(row).decode("ascii", "ignore")
        out.append(s.rstrip("\x00").strip())
    return out


class Exodus:
    def __init__(self, path):
        if Dataset is None:
            raise ImportError("read_exodus needs netCDF4 (pip install netCDF4)")
        self.path = path
        self.nc = Dataset(path, "r")
        v = self.nc.variables
        self.ndim = int(self.nc.dimensions["num_dim"].size)
        self.num_nodes = int(self.nc.dimensions["num_nodes"].size)
        self.num_elem = int(self.nc.dimensions["num_elem"].size)
        self.times = np.array(v["time_whole"][:]) if "time_whole" in v else np.zeros(0)
        axes = [v[n][:] for n in ("coordx", "coordy", "coordz") if n in v]
        self.coords = np.column_stack(axes)
        self.nodal_names = _names(v["name_nod_var"]) if "name_nod_var" in v else []
        self.element_names = _names(v["name_elem_var"]) if "name_elem_var" in v else []
        self.blocks = _names(v["eb_names"]) if "eb_names" in v else []
        self.connect = {}
        for name in v:
            if name.startswith("connect"):
                self.connect[name[len("connect"):]] = np.array(v[name][:]) - 1      # 1-based in the file
                self.connect[name[len("connect"):] + "_type"] = getattr(v[name], "elem_type", "")
        self.node_num_map = np.array(v["node_num_map"][:]) if "node_num_map" in v else np.arange(1, self.num_nodes + 1)

    def var(self, name, state=None):
        """A nodal variable by name, at one state or all states."""
        if name not in self.nodal_names:
            raise KeyError("%s not in %s" % (name, self.nodal_names))
        k = self.nodal_names.index(name) + 1
        data = self.nc.variables["vals_nod_var%d" % k]
        return np.array(data[state, :]) if state is not None else np.array(data[:, :])

    def positions(self, state):
        """The current configuration: the reference coordinates plus the displacement dX."""
        d = np.column_stack([self.var("dX_%d" % i, state) for i in range(self.ndim)])
        return self.coords + d

    def close(self):
        self.nc.close()


if __name__ == "__main__":
    p = sys.argv[1] if len(sys.argv) > 1 else "viz_IB2d/output.ex2"
    m = Exodus(p)
    print("%s: %dD, %d nodes, %d elements, blocks %s, %d states (t = %g .. %g)" % (p, m.ndim, m.num_nodes, m.num_elem, m.blocks, len(m.times), m.times[0] if len(m.times) else 0, m.times[-1] if len(m.times) else 0))
    print("nodal variables:", m.nodal_names)
    for key, c in m.connect.items():
        if not key.endswith("_type"):
            print("block %s: %s, %d elements of %d nodes" % (key, m.connect[key + "_type"], c.shape[0], c.shape[1]))
    if len(sys.argv) > 2:
        name = sys.argv[2]; s = int(sys.argv[3]) if len(sys.argv) > 3 else len(m.times) - 1
        a = m.var(name, s); print("%s at state %d (t = %g): min %g at node %d, max %g at node %d" % (name, s, m.times[s], a.min(), a.argmin(), a.max(), a.argmax()))
    m.close()
