# Using IB Software

Hands-on tutorials for immersed boundary software, with **IB2d**, **IBAMR** (including the immersed boundary finite element method, **IBFE**), **VisIt** for visualization, and **Planktos** for agent-based modeling in fluid flows. By **Laura A. Miller** (Department of Mathematics, University of Arizona), built from tutorials taught since 2013 at UNC Chapel Hill and the University of Arizona.

The theory behind these tools is in the companion series **[Fluid Dynamics and IBM Theory](https://github.com/equiphysics/Fluid-Dynamics-and-IBM-Theory)**.

> **This is the `master-tutorial` branch, a work in progress.** It holds the new, consolidated version of the tutorials while it is being written. The `main` branch keeps the original lectures until this version is finished and reviewed.

## Status (October 2026): being rewritten

The consolidated LaTeX version covers installing IBAMR with autoibamr, building examples with CMake, and current IBAMR releases. Every command and example in it was tested with IBAMR 0.16.0 (the version on the UA cluster) and 0.19.0 (the latest release). Chapters are added here as they are drafted.

| Part | Chapters | State |
|---|---|---|
| I · Getting set up | [1 Computing on Puma](1-Getting-Set-Up/1-Computing-Environment-UA-HPC.pdf), [2 Installing IBAMR with autoibamr](1-Getting-Set-Up/2-Installing-IBAMR-with-autoibamr.pdf), [3 Building and running an IBAMR application](1-Getting-Set-Up/3-Building-and-Running-IBAMR.pdf) | drafted |
| VI · Planktos | [34 What is Planktos?](Planktos/Planktos-1-What-is-Planktos.pdf), [35 Using Planktos](Planktos/Planktos-2-Using-Planktos.pdf) | existing decks |
| 0, II–V, VII, appendices | IB2d, IBAMR fundamentals, IBFE, VisIt, the examples guide, helper codes | in progress |

## Contents

| Folder | What it contains |
|---|---|
| [1-Getting-Set-Up/](1-Getting-Set-Up/) | Chapters 1–3 (LaTeX + PDF) |
| [Planktos/](Planktos/) | **What is Planktos?** and **Using Planktos** (LaTeX + PDF) |
| [examples/IB/](examples/IB/) | Immersed boundary examples, each with a CMake build, a Puma job script and a README: [01 rubber band](examples/IB/01-rubber-band/), [02 pulsatile channel](examples/IB/02-pulsatile-channel/) |
| [examples/IBFE/](examples/IBFE/) | Immersed boundary finite element examples: [01 tethered plate](examples/IBFE/01-tethered-plate/) |
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

## Feedback

Please let me know if you find any issues or have suggestions for extensions. You can open an issue on this repository.
