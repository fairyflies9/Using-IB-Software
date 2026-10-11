# Using IB Software

Hands-on tutorials for immersed boundary software, with **IB2d**, **IBAMR** (including the immersed boundary finite element method, **IBFE**), **VisIt** for visualization, and **Planktos** for agent-based modeling in fluid flows. By **Laura A. Miller** (Department of Mathematics, University of Arizona), built from tutorials taught since 2013 at UNC Chapel Hill and the University of Arizona.

The theory behind these tools is in the companion series **[Fluid Dynamics and IBM Theory](https://github.com/equiphysics/Fluid-Dynamics-and-IBM-Theory)**.

## Status (October 2026): being updated

A consolidated, corrected LaTeX version of these tutorials is in progress. It covers installing IBAMR with autoibamr, building examples with CMake, and current IBAMR releases (0.16–0.19). Until it is finished, the existing lectures below are available as they are. Some of them describe clusters that have since been retired and the older Makefile build, so check commands against the current IBAMR documentation at <https://ibamr.github.io>.

## Contents

| Folder | What it contains |
|---|---|
| [Planktos/](Planktos/) | **What is Planktos?** and **Using Planktos** (LaTeX + PDF, 2026) |
| [IBAMR Lectures/](IBAMR%20Lectures/) | Getting an HPC account and running a first simulation, IB method overview, structure files, boundary conditions, target points and springs, upstream examples, ConstraintIB, adding mass |
| [IBFE Lectures/](IBFE%20Lectures/) | Getting started with IBFE, making and moving meshes, 3D flow past objects, active tension, two boundaries, a walk through a main file, advection–diffusion, and a Gmsh tutorial |
| [Data Visualizationand Analysis/](Data%20Visualizationand%20Analysis/) | VisIt lectures: plotting IBAMR data, 3D visualization, finite element boundaries, VisIt on a cluster |
| [ib2d Lectures/](ib2d%20Lectures/) | Introduction to IB2d and an IB2d practical |
| [Examples/](Examples/) | Example codes from UNC and University of Arizona courses |
| [MATLAB codes/](MATLAB%20codes/) | Small MATLAB exercises (heat equation, stiff ODEs, IB geometry and springs) |
| [Old files/](Old%20files/) | Earlier versions kept for reference |

## Credits

Material in these tutorials was developed with many students and colleagues over the years; individual decks credit their contributors and sources.

Claude (Anthropic) was used to organize, combine, and format more than twelve years (2013–2026) of the instructor's tutorial notes from courses and workshops at several universities.

## License

- **Slides, text and figures:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). You may share and adapt them for any purpose, as long as you give credit.
- **Example code and scripts:** [BSD 3-Clause](LICENSE-CODE).
- **Exceptions:** files that carry their own copyright notice or credit another author keep their original terms. The example programs adapted from IBAMR keep IBAMR's BSD 3-Clause notice, figures from other sources are credited where they appear, and the papers in `papers/` are under their publishers' licenses.

To credit these tutorials, cite: L. A. Miller, *Using IB Software*, https://github.com/fairyflies9/Using-IB-Software.

## Feedback

Please let me know if you find any issues or have suggestions for extensions. You can open an issue on this repository.
