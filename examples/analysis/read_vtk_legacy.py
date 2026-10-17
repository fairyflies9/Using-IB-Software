"""read_vtk_legacy.py: read the legacy (ASCII) VTK files that VisIt exports and that IB2d writes, with nothing but
NumPy (chapter 33). For anything beyond this, use meshio (pip install meshio) or pyvista, which read every VTK
flavour in one line: m = meshio.read("file.vtk"); m.points, m.cells, m.point_data.

Handles the dataset types these tutorials meet:
    RECTILINEAR_GRID    VisIt's Resample operator exported as VTK (x, y, z coordinate lists + point data)
    STRUCTURED_POINTS   IB2d's .vtk output (origin + spacing + point data)
    UNSTRUCTURED_GRID   an IBFE mesh exported from VisIt, or IB2d's point files (points, cells, point data);
                        both the 4.x cell layout and the 5.1 OFFSETS/CONNECTIVITY layout
    POLYDATA            Lagrangian points exported from VisIt (points [+ vertices])
Returns a dict: type, dims (nx, ny, nz) when gridded, x/y/z axes (RECTILINEAR) or origin/spacing (STRUCTURED),
points (N, 3) for the unstructured kinds, cells (list of index lists), and data: {name: array}; gridded arrays are
reshaped [z, y, x] (and squeezed), vectors keep a trailing component axis. FIELD data (VisIt's TIME, CYCLE) are in
'field'. The origin of these readers is C. Strickland's read_vtk_data.py (2017, with the vtk module) and
N. Battista's read_Structured_Vector_Field_Data_From_vtk.m (2017).
"""
import sys

import numpy as np


def _tokens(path):
    with open(path, "r") as f:
        text = f.read()
    return text.split("\n")


def read_vtk(path):
    lines = _tokens(path)
    if not lines[0].startswith("# vtk DataFile"):
        raise ValueError("%s is not a legacy VTK file" % path)
    if lines[2].strip().upper() != "ASCII":
        raise ValueError("binary legacy VTK: use meshio or the vtk module")
    out = dict(path=path, title=lines[1].strip(), data={}, field={}, cells=[])
    i = 3
    n = len(lines)
    dims = None
    npts = None
    section = None            # POINT_DATA or CELL_DATA

    def numbers(count, start):
        """count floats starting at line index start; returns (array, next line index)."""
        vals = []
        j = start
        while len(vals) < count and j < n:
            vals.extend(float(v) for v in lines[j].split())
            j += 1
        return np.array(vals[:count]), j

    while i < n:
        line = lines[i].strip()
        if not line:
            i += 1; continue
        key = line.split()[0].upper()
        parts = line.split()
        if key == "DATASET":
            out["type"] = parts[1].upper(); i += 1
        elif key == "DIMENSIONS":
            dims = tuple(int(v) for v in parts[1:4]); out["dims"] = dims; npts = dims[0] * dims[1] * dims[2]; i += 1
        elif key == "ORIGIN":
            out["origin"] = tuple(float(v) for v in parts[1:4]); i += 1
        elif key == "SPACING":
            out["spacing"] = tuple(float(v) for v in parts[1:4]); i += 1
        elif key in ("X_COORDINATES", "Y_COORDINATES", "Z_COORDINATES"):
            cnt = int(parts[1]); arr, i = numbers(cnt, i + 1); out[key[0].lower()] = arr
        elif key == "POINTS":
            cnt = int(parts[1]); arr, i = numbers(3 * cnt, i + 1); out["points"] = arr.reshape(cnt, 3); npts = cnt
        elif key in ("CELLS", "VERTICES", "LINES", "POLYGONS"):
            cnt, size = int(parts[1]), int(parts[2])
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and lines[j].strip().upper().startswith("OFFSETS"):
                # VTK 5.1 layout (VTK 9, IB2d's Python writer): cnt = number of cells + 1 offsets, then the
                # connectivity list of `size` entries; a cell k spans conn[off[k]:off[k+1]]
                off, i = numbers(cnt, j + 1); off = off.astype(int)
                while i < len(lines) and not lines[i].strip().upper().startswith("CONNECTIVITY"):
                    i += 1
                conn, i = numbers(size, i + 1); conn = conn.astype(int)
                out["cells"] = [conn[off[k]:off[k + 1]].tolist() for k in range(cnt - 1)]
            else:
                # VTK 4.x layout: size entries of "m i_1 ... i_m"
                arr, i = numbers(size, i + 1)
                arr = arr.astype(int); k = 0; cells = []
                while k < size:
                    m = arr[k]; cells.append(arr[k + 1:k + 1 + m].tolist()); k += 1 + m
                out["cells"] = cells
        elif key == "CELL_TYPES":
            cnt = int(parts[1]); arr, i = numbers(cnt, i + 1); out["cell_types"] = arr.astype(int)
        elif key in ("POINT_DATA", "CELL_DATA"):
            section = key; out[key.lower() + "_count"] = int(parts[1]); i += 1
        elif key in ("SCALARS", "VECTORS"):
            name = parts[1]; comp = 1 if key == "SCALARS" else 3
            if key == "SCALARS" and len(parts) > 3:
                comp = int(parts[3])
            i += 1
            if lines[i].strip().upper().startswith("LOOKUP_TABLE"):
                i += 1
            cnt = out.get("point_data_count", npts) if section == "POINT_DATA" else out.get("cell_data_count")
            arr, i = numbers(comp * cnt, i)
            out["data"][name] = _shape(arr, comp, cnt, dims if section == "POINT_DATA" else None)
        elif key == "FIELD":
            nfield = int(parts[2]); i += 1
            for _ in range(nfield):
                while i < n and not lines[i].strip():
                    i += 1
                hp = lines[i].split(); name, comp, cnt, dtype = hp[0], int(hp[1]), int(hp[2]), hp[3].lower()
                if dtype == "string":
                    i += 1; val = lines[i].strip(); i += 1
                    (out["field"] if section is None else out["data"])[name] = val
                    continue
                arr, i = numbers(comp * cnt, i + 1)
                target = out["data"] if section in ("POINT_DATA", "CELL_DATA") else out["field"]
                target[name] = _shape(arr, comp, cnt, dims if section == "POINT_DATA" else None)
        elif key in ("METADATA", "INFORMATION"):
            i += 1
            while i < n and lines[i].strip() and not lines[i].split()[0].isupper():
                i += 1
        else:
            i += 1
    return out


def _shape(arr, comp, cnt, dims):
    if comp > 1:
        arr = arr.reshape(cnt, comp)
    if dims is not None:
        shp = (dims[2], dims[1], dims[0]) + ((comp,) if comp > 1 else ())
        arr = arr.reshape(shp)
        arr = arr.squeeze() if comp == 1 else arr.reshape([d for d in shp[:3] if d > 1] + [comp])
    return arr


def grid_axes(v):
    """x, y, z axes of a gridded file (RECTILINEAR: the lists; STRUCTURED_POINTS: origin + spacing)."""
    if v["type"] == "RECTILINEAR_GRID":
        return v["x"], v["y"], v["z"]
    nx, ny, nz = v["dims"]; o, s = v["origin"], v["spacing"]
    return o[0] + s[0] * np.arange(nx), o[1] + s[1] * np.arange(ny), o[2] + s[2] * np.arange(nz)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        v = read_vtk(p)
        print(p, v["type"], "dims", v.get("dims"), "points", None if "points" not in v else v["points"].shape, "cells", len(v["cells"]))
        for k, a in v["data"].items():
            print("   data", k, getattr(a, "shape", a), "min %g max %g" % (np.min(a), np.max(a)) if hasattr(a, "shape") else "")
        for k, a in v["field"].items():
            print("   field", k, a)
