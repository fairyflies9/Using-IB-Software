# examples/analysis: readers for IBAMR's output, in Python and MATLAB/Octave

Small, dependency-light readers used by the chapters of *Using IB Software*; each file's docstring says how to call it.

| file | reads or writes | chapter |
|---|---|---|
| `hier_data.py`, `read_hier_data.m`, `read_input.m` | the `X.*`, `F.*` text files of the examples' `output_data` (PETSc ASCII); constants from an input file | 11 |
| `leaf_forces.py`, `leaf_forces.m` | a worked example: the drag coefficient of IB/03 from the forces | 11 |
| `samrai_dumps.py`, `samrai_dumps.m` | the VisIt dumps (`viz_IB2d/visit_dump.NNNNN`, SAMRAI HDF5) straight into NumPy or MATLAB, and onto a uniform grid of one level; the list of frames with their times; the flux across a line | 33 |
| `flow_rate.py` | the flow rate across vertical or horizontal lines against time, from the dumps | 33 |
| `resample_export.py` | runs inside VisIt's Python (`visit -nowin -cli -s resample_export.py -- ...`): Resample operator + Export Database to VTK over a series of frames, with the work-arounds for VisIt 3.5 headless; with a parallel engine (`-np`) it writes the serial engine's file (the distributed resample off) | 33, 32, 31 |
| `visit_3d.py` | runs inside VisIt's Python (`visit -nowin -cli -s visit_3d.py -- plate|glyco <viz_IB3d folder> <out dir>`): the 3D pictures of chapter 27 for IBFE/10 and IB/08 (the body as points, spheres or a displaced mesh; translucent isosurfaces of the vorticity; vectors, colour and contour lines on slices; ThreeSlice; streamlines with the IntegralCurve operator), with the VisIt 3.5 work-arounds commented | 27, 32 |
| `visit_queries.py` | runs inside VisIt's Python (`visit -nowin -cli -s visit_queries.py -- <dumps.visit> <out dir> [box=... point=... line=...]`): the data-analysis recipes of chapter 29 on a 2D run: a Box and Average Value frame by frame and over time, a node pick over time, lineouts, the flow rate across any line, curves exported as text | 29 |
| `read_curve.py`, `read_curve.m` | VisIt's `.curve` files (a `# name` line before each curve, then `x y` pairs) into NumPy, or a MATLAB/Octave struct array, keeping several curves in one file apart | 29 |
| `templates/` | `analysis_protocol.md`, `data_sheet.md`, `analysis_report.md`: the written record of an analysis (after Lindsay Waldrop's VisIt guide), each with chapter 29's IB/11 analysis as the example | 29 |
| `visit_movie_frames.py` | runs inside VisIt's Python (`visit -nowin -cli -s visit_movie_frames.py -- <viz folder or dumps.visit> <out dir> [key=value ...]`): the frames of a movie, one PNG per dump, with fixed colour limits, the structure, a time stamp and no Subset plot, every time slider stepped; `frames.csv` (frame, dump, time); a session for `visit -movie` if asked | 30 |
| `visit_frames.slurm` | a Slurm job for Puma: `visit_movie_frames.py` on a finished run's `viz_IB2d` (or `viz_IB3d`) without a display, the frames counted, and `make_movie.py` if an `ffmpeg` is found; submit it from the run's folder (not yet run on Puma) | 31 |
| `make_movie.py` | a folder of frames to an H.264 MP4 (yuv420p, even size, any numbering) or a GIF, with ffmpeg | 30 |
| `movie_clean.py` | frames already rendered with the Subset plot of `levels` left in: the thin coloured lines of the patch boundaries replaced by the colour around them (needs `Pillow`) | 30 |
| `read_vtk_legacy.py`, `read_vtk_legacy.m` | legacy ASCII VTK files (VisIt's exports: rectilinear, unstructured, polydata; IB2d's structured points) | 33 |
| `read_exodus.py`, `read_exodus.m` | the ExodusII file of an IBFE run (`output.ex2`): times, coordinates, connectivity, nodal fields, current positions | 33, 28 |
| `hier_data_h5.py` | the HDF5 state dumps the upstream examples write (`hier_data.NNNNN.samrai.PPPPP`): patches with the solver's cell and side data | 33 |
| `piv_to_vtk.py` | two text arrays (PIV components, or any gridded field) to a VTK vector field for VisIt | 33, 29 |
| `vtk_for_planktos.py` | `resample_export.py`'s VTK exports of a 3D run made readable by Planktos's `read_IBAMR3d_vtk_data`: the vector made the active one, the files numbered `IBAMR_db_000.vtk`, `IBAMR_db_001.vtk`, ... (needs `vtk`) | 35 |

Python 3 with `numpy`; `h5py` for the SAMRAI files, `netCDF4` for Exodus, `vtk` or `pyvista` only if you want them (`apt install python3-h5py python3-netcdf4 python3-vtk9` on Ubuntu, `pip install h5py netCDF4` elsewhere). VisIt 3.5's own Python (3.13) has NumPy, VTK and Pillow but not h5py, netCDF4, pyvista, pandas, SciPy or matplotlib (measured, chapter 32); `resample_export.py`, `visit_3d.py`, `visit_queries.py` and `visit_movie_frames.py` call VisIt's functions and run inside VisIt, the others in any Python 3 with the packages above. The `.m` files were run in Octave 8.4 (with the `netcdf` package for `read_exodus.m`) except `samrai_dumps.m`, which needs MATLAB's `h5read`.

Tested on IBAMR 0.19.0 output (chapters 11, 28 and 33 give the numbers): `samrai_dumps.py` reproduces the files' own extents and agrees with VisIt's Resample export to single precision; `read_exodus.py/.m` reproduce chapter 28's Pick values.
