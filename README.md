# Using IB Software

Hands-on tutorials for immersed boundary software, with **IB2d**, **IBAMR** (including the immersed boundary finite element method, **IBFE**), **VisIt** for visualization, and **Planktos** for agent-based modeling in fluid flows. By **Laura A. Miller** (Department of Mathematics, University of Arizona), built from tutorials taught since 2013 at UNC Chapel Hill and the University of Arizona.

The theory behind these tools is in the companion series **[Fluid Dynamics and IBM Theory](https://github.com/fairyflies9/Fluid-Dynamics-and-IBM-Theory)**.

> **This is the `master-tutorial` branch, a work in progress.** It holds the new, consolidated version of the tutorials while it is being written. The `main` branch keeps the original lectures until this version is finished and reviewed.

## Status (October 2026): being rewritten

The consolidated LaTeX version covers the software landscape and the path from an organism to a mesh, installing IBAMR with autoibamr, building examples with CMake, and current IBAMR releases. The examples and the build commands were tested with IBAMR 0.16.0 (the version on the UA cluster) and 0.19.0 (the latest release). Example IB/01 has also been built and run on Puma with the commands in chapters 1-3 (4 min 14 s on 4 cores); the other job scripts follow the same pattern. Chapters are added here as they are drafted. Part X, the archive, keeps what the course used before: the retired clusters, the hand-built installs of 2011-2019, the old course code mapped to current IBAMR, and the course logistics of 2013-2024, each slide labelled legacy.

| Part | Chapters | State |
|---|---|---|
| 0 · Front matter | [0.1 About these notes](0-Front-Matter/0-1-About-These-Notes.pdf), [0.2 Roadmap and how to use](0-Front-Matter/0-2-Roadmap-and-How-to-Use.pdf) | drafted |
| I · Getting set up | [1 Computing on Puma](1-Getting-Set-Up/1-Computing-Environment-UA-HPC.pdf), [1b Choosing software and building geometries](1-Getting-Set-Up/1b-Choosing-Software-and-Building-Geometries.pdf), [2 Installing IBAMR with autoibamr](1-Getting-Set-Up/2-Installing-IBAMR-with-autoibamr.pdf), [3 Building and running an IBAMR application](1-Getting-Set-Up/3-Building-and-Running-IBAMR.pdf) | drafted |
| II · IB2d | [4a Introduction to IB2d and its file formats](2-IB2d/4a-Introduction-to-IB2d-and-File-Formats.pdf), [4b The IB2d practical, and VisIt for IB2d](2-IB2d/4b-The-IB2d-Practical-and-VisIt-for-IB2d.pdf), [4c Moving boundaries, and making your own example](2-IB2d/4c-Moving-Boundaries-and-Your-Own-Example.pdf), [4d Stability and convergence: a lab](2-IB2d/4d-Stability-and-Convergence-Lab.pdf), [4e The model gallery, and muscle models](2-IB2d/4e-Model-Gallery-and-Muscle-Models.pdf), [4f Meshes from images: MeshmerizeMe](2-IB2d/4f-Meshes-From-Images-MeshmerizeMe.pdf) | complete |
| III · IBAMR fundamentals | [5 The immersed boundary method and numerical considerations](3-IBAMR-Fundamentals/5-The-IB-Method-and-Numerical-Considerations.pdf), [6 Structure files](3-IBAMR-Fundamentals/6-Structure-Files.pdf), [7 Boundary conditions and domain set-up](3-IBAMR-Fundamentals/7-Boundary-Conditions-and-Domain-Setup.pdf), [8a Changing physical parameters wisely](3-IBAMR-Fundamentals/8a-Changing-Physical-Parameters-Wisely.pdf), [8b Non-dimensionalization](3-IBAMR-Fundamentals/8b-Non-dimensionalization.pdf), [9a Target points, springs and multiple boundaries](3-IBAMR-Fundamentals/9a-Target-Points-Springs-and-Multiple-Boundaries.pdf), [9b Custom spring forces and active pumping](3-IBAMR-Fundamentals/9b-Custom-Spring-Forces-and-Active-Pumping.pdf), [10 Resting curvature and beams](3-IBAMR-Fundamentals/10-Resting-Curvature-and-Beams.pdf), [11 Output and analysis of forces](3-IBAMR-Fundamentals/11-Output-and-Analysis-of-Forces.pdf), [12 3D simulations](3-IBAMR-Fundamentals/12-3D-Simulations.pdf), [13 Adding mass](3-IBAMR-Fundamentals/13-Adding-Mass.pdf), [14 Constraint IB](3-IBAMR-Fundamentals/14-ConstraintIB.pdf), [15 Tour of the upstream examples](3-IBAMR-Fundamentals/15-Tour-of-the-Upstream-Examples.pdf), [16 What can go wrong, convergence tests and debugging](3-IBAMR-Fundamentals/16-What-Can-Go-Wrong-Convergence-and-Debugging.pdf) | complete |
| IV · IBFE | [17 Getting started with IBFE](4-IBFE/17-Getting-Started-with-IBFE.pdf), [18 Creating meshes](4-IBFE/18-Creating-Meshes.pdf), [19 PK1 stress functions and body forces](4-IBFE/19-PK1-Stress-Functions-and-Body-Forces.pdf), [20 Fibre tension and active stress](4-IBFE/20-Fiber-Tension-and-Active-Stress.pdf), [21 Two or more meshes](4-IBFE/21-Two-or-More-Meshes.pdf), [22 3D flow past objects and the flow tank](4-IBFE/22-3D-Flow-Past-Objects-and-the-Flow-Tank.pdf), [23 Walking through an IBFE main file](4-IBFE/23-Walking-through-an-IBFE-Main-File.pdf), [24 IBFE with advection–diffusion](4-IBFE/24-IBFE-with-Advection-Diffusion.pdf), [25 Tour of IBAMR's own IBFE examples](4-IBFE/25-Tour-of-the-Upstream-IBFE-Examples.pdf) | complete |
| V · VisIt | [26 Getting started, and making it look better](5-VisIt/26-Getting-Started-and-Making-It-Look-Better.pdf), [27 VisIt in 3D: isosurfaces, slices, vectors and streamlines](5-VisIt/27-VisIt-in-3D.pdf), [28 Lagrangian and finite-element data](5-VisIt/28-Lagrangian-and-Finite-Element-Data.pdf), [29 Data analysis](5-VisIt/29-Data-Analysis-in-VisIt.pdf), [30 Making movies](5-VisIt/30-Making-Movies.pdf), [31 VisIt on the cluster](5-VisIt/31-VisIt-on-the-Cluster.pdf), [32 VisIt from the command line and Python](5-VisIt/32-VisIt-from-the-Command-Line-and-Python.pdf), [33 Converting between data types; exporting to MATLAB and Python](5-VisIt/33-Converting-Data-and-Exporting-to-MATLAB-and-Python.pdf) | complete |
| VI · Planktos | [34 What is Planktos?](Planktos/Planktos-1-What-is-Planktos.pdf), [35 Using Planktos](Planktos/Planktos-2-Using-Planktos.pdf) | complete |
| VII · Examples guide | [36 Catalogue of examples](7-Examples-Guide/36-Catalogue-of-Examples.pdf) | complete |
| X · Archive (legacy) | [X1 Retired clusters and workflows](X-Archive/X1-Retired-Clusters-and-Workflows.pdf), [X2 Historical install recipes](X-Archive/X2-Historical-Install-Recipes.pdf), [X3 Old IBAMR and libMesh code, mapped to current code](X-Archive/X3-Old-IBAMR-and-libMesh-Code.pdf), [X4 Course logistics](X-Archive/X4-Course-Logistics.pdf) | complete |
| Appendices | [A MATLAB and Python helper codes](8-Appendices/A-MATLAB-and-Python-Helper-Codes.pdf), [B Glossary, references and credits](8-Appendices/B-Glossary-References-and-Credits.pdf), [C Exercise and homework bank](8-Appendices/C-Exercise-and-Homework-Bank.pdf) | complete |

**Videos.** The recordings that the original lectures refer to were class recordings on the course site and were never public; chapter 0.1 lists what they covered, and new recordings will follow the new chapters. The four IB2d video tutorials by Nick Battista are public: [1 the IB method and IB2d](https://youtu.be/PJyQA0vwbgU), [2 what comes with IB2d](https://youtu.be/jSwCKq0v84s), [3 building a geometry and its input files](https://youtu.be/I3TLpyEBXfE), [4 visualizing the output in VisIt](https://youtu.be/4D4ruXbeCiQ).

## Contents

| Folder | What it contains |
|---|---|
| [0-Front-Matter/](0-Front-Matter/) | Chapters 0.1 and 0.2: about these notes (provenance, contributors, the list of lecture videos) and the roadmap (LaTeX + PDF) |
| [1-Getting-Set-Up/](1-Getting-Set-Up/) | Chapters 1, 1b, 2 and 3 (LaTeX + PDF) |
| [2-IB2d/](2-IB2d/) | Part II, chapters 4a to 4f (LaTeX + PDF) |
| [3-IBAMR-Fundamentals/](3-IBAMR-Fundamentals/) | Part III, chapters 5–16 (LaTeX + PDF), complete |
| [4-IBFE/](4-IBFE/) | Part IV, chapters 17–25 (LaTeX + PDF), complete |
| [5-VisIt/](5-VisIt/) | Part V, chapters 26–33 (LaTeX + PDF), complete |
| [Planktos/](Planktos/) | Part VI, chapters 34 (**What is Planktos?**) and 35 (**Using Planktos**) (LaTeX + PDF), complete |
| [7-Examples-Guide/](7-Examples-Guide/) | Part VII, chapter 36: the catalogue of examples, one page per example (LaTeX + PDF) |
| [8-Appendices/](8-Appendices/) | Appendices A (every maintained MATLAB script beside its Python version), B (glossary, references with DOIs, software versions, contributors, pictures from elsewhere, licences) and C (the exercise and homework bank, problems only) (LaTeX + PDF) |
| [X-Archive/](X-Archive/) | Part X, the archive, labelled legacy: X1 retired clusters and workflows (the lab servers, UNC's Kure, KillDevil, Dogwood and Longleaf, Arizona's Ocelote and El Gato), X2 historical install recipes (2011-2019), X3 old IBAMR and libMesh code mapped to current code, X4 course logistics (LaTeX + PDF) |
| [examples/IB/](examples/IB/) | Immersed boundary examples, each with a CMake build, a Puma job script and a README: [01 rubber band](examples/IB/01-rubber-band/), [02 pulsatile channel](examples/IB/02-pulsatile-channel/), [03 tethered beam](examples/IB/03-tethered-beam/), [04 moving cylinders](examples/IB/04-moving-cylinders/), [06 growing springs](examples/IB/06-growing-springs/), [07 moving plates](examples/IB/07-moving-plates/), [08 glycocalyx 3D](examples/IB/08-glycocalyx-3d/), [09 curling beam](examples/IB/09-curling-beam/), [10 jellyfish bell](examples/IB/10-jellyfish-bell/), [11 heart-tube pump](examples/IB/11-heart-tube-pump/), [12 spider ballooning](examples/IB/12-spider-ballooning/), [13 carotid artery, horse and human](examples/IB/13-carotid-bifurcation/) |
| [examples/IB2d/](examples/IB2d/) | The tutorial's own pyIB2d examples (chapters 4c-4f): the moving band, the sawtooth pump, the pulsing heart, the stability lab (a parametrised rubber band, the sweep that made chapter 4d's tables, the shape analysis), the muscle models (length-tension, force-velocity, the crossbridge derivation checked numerically, the heart tube's activation wave, a calcium activation model), and meshes from SVG drawings (an equal-distance point sampler, and IB2d's MeshmerizeMe starfish ported to Python), with READMEs |
| [examples/ConstraintIB/](examples/ConstraintIB/) | Constraint immersed boundary examples (chapter 14), each with a CMake build, a Puma job script and a README: [01 oscillating cylinder](examples/ConstraintIB/01-oscillating-cylinder/), [02 impulsively started cylinder](examples/ConstraintIB/02-impulsively-started-cylinder/), [03 swimming eel](examples/ConstraintIB/03-eel-swimming/) |
| [examples/IBFE/](examples/IBFE/) | Immersed boundary finite element examples: [01 tethered plate](examples/IBFE/01-tethered-plate/), [05 gmsh triangle](examples/IBFE/05-gmsh-triangle/), [06 active tension](examples/IBFE/06-active-tension/), [08 plate hits circle](examples/IBFE/08-plate-hits-circle/), [10 flow tank plate 3D](examples/IBFE/10-flow-tank-plate-3d/), [12 advection–diffusion](examples/IBFE/12-advection-diffusion/) |
| [examples/analysis/](examples/analysis/) | Readers for the examples' position and force files in Python and MATLAB/Octave and the drag-and-lift analysis of IB/03 (chapter 11); the VisIt scripts of Part V (frames, queries, 3D pictures, resampling and export, a Slurm job) and `vtk_for_planktos.py` (chapter 35) |
| [examples/Planktos/](examples/Planktos/) | Planktos on this series' flows (chapters 34 and 35): chapter 4f's IB2d starfish (density estimates, capture, FTLE maps, Vicsek alignment), IBFE/10's flow tank with a plate through VisIt, and the first run of chapter 35 |
| [examples/support/](examples/support/) | The course's MATLAB exercises (the heat equation, a stiff equation, checking and plotting structure files) beside their Python versions, with the rubber band they were run on (Appendix A) |
| [examples/legacy/](examples/legacy/) | The course example codes as they were, from UNC and the University of Arizona. They use the old Makefile build; the folders above replace them one by one. |
| [originals/](originals/) | The original lectures (IBAMR, IBFE, VisIt, IB2d), the MATLAB exercises, and older files, kept unchanged for reference |
| [pictures/](pictures/) | Figures used by the LaTeX decks |
| [papers/](papers/) | Open-access papers referred to in the tutorials |
| `ib-tutorials.sty` | The shared slide style |

### Building the slides

Each deck compiles on its own with `pdflatex`, from the repository root or from its own folder, for example:

```bash
cd 1-Getting-Set-Up
pdflatex 3-Building-and-Running-IBAMR.tex
```

### Line endings

The files in `examples/` must keep Unix line endings: IBAMR stops with `Illegal character token in input` when an input file has Windows line endings. The `.gitattributes` file makes Git check them out that way on every system, including Windows.

## Credits

Material in these tutorials was developed with many students and colleagues over the years; individual decks credit their contributors and sources.

Claude (Anthropic) was used to organize, combine, and format more than twelve years (2013–2026) of the instructor's tutorial notes from courses and workshops at several universities.

## License

- **Slides, text and figures:** [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE). You may share and adapt them for any purpose, as long as you give credit.
- **Example code and scripts:** [BSD 3-Clause](LICENSE-CODE).
- **Exceptions:** files that carry their own copyright notice or credit another author keep their original terms. The example programs adapted from IBAMR keep IBAMR's BSD 3-Clause notice, figures from other sources are credited where they appear, and the papers in `papers/` are under their publishers' licenses.

To credit these tutorials, cite: Miller, L. A. (2026). *Using IB Software: tutorials for IB2d, IBAMR, VisIt and Planktos.* https://github.com/fairyflies9/Using-IB-Software

The author also directs [EquiPhysics](https://equiphysics.org), a nonprofit that brings horse lovers to mathematics; these tutorials are shared there too.
## Feedback

Please let me know if you find any issues or have suggestions for extensions. You can open an issue on this repository.
