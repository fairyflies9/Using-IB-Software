# extras

`Beam_IBFE_Mesh2D.m` (or its Python version, `python3 beam_ibfe_mesh2d.py`, which writes an identical file) writes `IBFE_Mesh2D_128.poly`, a Triangle input file for a 1.0 by 0.25 rectangle. This example does **not** read either file: it reads `IBFE_Mesh2D_128.mat`, a 1.0 by 0.0312 plate made with MATLAB's PDE Toolbox (see the main README).

They are kept here because the course versions shipped them, and because a `.poly` file is one way to make a triangle mesh with the Triangle program (chapter 18).
