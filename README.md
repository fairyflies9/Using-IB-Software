# Using IB Software

Hands-on tutorials for immersed boundary software, with **IB2d**, **IBAMR** (including the immersed boundary finite element method, **IBFE**), **VisIt** for visualization, and **Planktos** for agent-based modeling in fluid flows. By **Laura A. Miller** (Department of Mathematics, University of Arizona), built from tutorials taught since 2013 at UNC Chapel Hill and the University of Arizona.

The theory behind these tools is in the companion series **[Fluid Dynamics and IBM Theory](https://github.com/equiphysics/Fluid-Dynamics-and-IBM-Theory)**.

> **This is the `master-tutorial` branch, a work in progress.** It holds the new, consolidated version of the tutorials while it is being written. The `main` branch keeps the original lectures until this version is finished and reviewed.

## Status (October 2026): being rewritten

The consolidated LaTeX version covers the software landscape and the path from an organism to a mesh, installing IBAMR with autoibamr, building examples with CMake, and current IBAMR releases. The examples and the build commands were tested with IBAMR 0.16.0 (the version on the UA cluster) and 0.19.0 (the latest release). Example IB/01 has also been built and run on Puma with the commands in chapters 1-3 (4 min 14 s on 4 cores); the other job scripts follow the same pattern. Chapters are added here as they are drafted.

| Part | Chapters | State |
|---|---|---|
| 0 · Front matter | [0.1 About these notes](0-Front-Matter/0-1-About-These-Notes.pdf), [0.2 Roadmap and how to use](0-Front-Matter/0-2-Roadmap-and-How-to-Use.pdf) | drafted |
| I · Getting set up | [1 Computing on Puma](1-Getting-Set-Up/1-Computing-Environment-UA-HPC.pdf), [1b Choosing software and building geometries](1-Getting-Set-Up/1b-Choosing-Software-and-Building-Geometries.pdf), [2 Installing IBAMR with autoibamr](1-Getting-Set-Up/2-Installing-IBAMR-with-autoibamr.pdf), [3 Building and running an IBAMR application](1-Getting-Set-Up/3-Building-and-Running-IBAMR.pdf) | drafted |
| VI · Planktos | [34 What is Planktos?](Planktos/Planktos-1-What-is-Planktos.pdf), [35 Using Planktos](Planktos/Planktos-2-Using-Planktos.pdf) | existing decks |
| III · IBAMR fundamentals | [5 The immersed boundary method and numerical considerations](3-IBAMR-Fundamentals/5-The-IB-Method-and-Numerical-Considerations.pdf), [6 Structure files](3-IBAMR-Fundamentals/6-Structure-Files.pdf) | drafted; chapters 7–16 in progress |
| II, IV, V, VII, appendices | IB2d, IBFE, VisIt, the examples guide, helper codes | in progress |

## Contents

| Folder | What it contains |
|---|---|
| [0-Front-Matter/](0-Front-Matter/) | Chapters 0.1 and 0.2: about these notes (provenance, contributors, the list of lecture videos) and the roadmap (LaTeX + PDF) |
| [1-Getting-Set-Up/](1-Getting-Set-Up/) | Chapters 1, 1b, 2 and 3 (LaTeX + PDF) |
| [3-IBAMR-Fundamentals/](3-IBAMR-Fundamentals/) | Part III, starting with chapter 5 (LaTeX + PDF) |
| [Planktos/](Planktos/) | **What is Planktos?** and **Using Planktos** (LaTeX + PDF) |
| [examples/IB/](examples/IB/) | Immersed boundary examples, each with a CMake build, a Puma job script and a README: [01 rubber band](examples/IB/01-rubber-band/), [02 pulsatile channel](examples/IB/02-pulsatile-channel/), [03 tethered beam](examples/IB/03-tethered-beam/), [04 moving cylinders](examples/IB/04-moving-cylinders/), [06 growing springs](examples/IB/06-growing-springs/), [07 moving plates](examples/IB/07-moving-plates/), [08 glycocalyx 3D](examples/IB/08-glycocalyx-3d/) |
| [examples/IBFE/](examples/IBFE/) | Immersed boundary finite element examples: [01 tethered plate](examples/IBFE/01-tethered-plate/), [05 gmsh triangle](examples/IBFE/05-gmsh-triangle/), [06 active tension](examples/IBFE/06-active-tension/), [08 plate hits circle](examples/IBFE/08-plate-hits-circle/), [10 flow tank plate 3D](examples/IBFE/10-flow-tank-plate-3d/), [12 advection–diffusion](examples/IBFE/12-advection-diffusion/) |
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

To credit these tutorials, cite: L. A. Miller, *Using IB Software*, https://github.com/fairyflies9/Using-IB-Software.

## Feedback

Please let me know if you find any issues or have suggestions for extensions. You can open an issue on this repository.
