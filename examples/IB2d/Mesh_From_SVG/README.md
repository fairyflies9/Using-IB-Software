# Mesh_From_SVG: Lagrangian points from an SVG drawing, and the starfish in a channel

Chapter 4f of *Using IB Software* (meshes from images with MeshmerizeMe). MeshmerizeMe
(https://github.com/dmsenter89/MeshmerizeMe; Senter et al., *Bioinspir. Biomim.* 16 (2021) 016008) turns the
paths of an SVG file into immersed-boundary points about `ds = dx/2` apart. This folder has a small sampler that
does the same job, for checking MeshmerizeMe's output and for drawings of your own, and a pyIB2d port of IB2d's
MeshmerizeMe starfish example built with it.

| file | what |
|---|---|
| `svg_to_vertex.py drawing.svg [options]` | reads `Lx`, `Ly`, `Nx`, `string_name` from `./input2d` (or `--input2d`), parses the SVG's paths (M L H V C S Q T A Z, absolute and relative, compact numbers, arcs) and basic shapes, joins consecutive pieces into contours, maps SVG space (y down) to `[0, Lx] x [0, Ly]` (y up), and writes `string_name.vertex` with neighbours a Euclidean distance `ds = Lx/(2 Nx)` apart (`--mode chord`, the default; `--mode arc` for equal arc length). Options: `--fit uniform|stretch` (one scale, the default, or each axis to the box), `--size S` and `--center X,Y` (resize the drawing's largest dimension and move its centre), `--spacing DS`, `--name NAME`, `--plot`. NumPy only (Matplotlib for `--plot`). |
| `Starfish_Channel/` | the starfish of `matIB2d/Examples/Example_Meshmerize_Me/Flow_Around_Starfish` as a Python example at `512 x 128`: `make_starfish_channel.py` (geometry from the SVG, walls, targets), `please_Compute_External_Forcing.py` (the MATLAB forcing, ported), `input2d`, `main2d.py`. See its README. |

## How the points are placed

Neighbouring points should be the same Euclidean distance apart (the condition MeshmerizeMe imposes, equation 1 of
the paper, which it solves by gradient descent). Here the curve is sampled finely (48 points per Bezier piece), and a
walk places each next point where a circle of radius `h` around the last one leaves the curve. The chord `h` is found
by bisection near `ds` so that the last chord (to the end of an open contour, or back to the start of a closed one)
is `h` too. A closed contour that cannot close evenly from its first point (a hook near the start) is retried from
11 other starting points; if none works, that contour falls back to equal arc length and the script says so.

## Tests (October 2026, in a unit box at 256 x 256, ds = 1/512)

| SVG | points | chord / ds |
|---|---|---|
| the design notes' wing, `M20 150 L200 120 Q280 150 200 180 Z` in 300 x 300 | 801 | 1.0005 |
| a circle of radius 40 in a 100 x 100 view box (radius 0.4) | 1287 (2 pi r / ds = 1286.8) | 0.9999 |
| `Flow_Around_Starfish/starfish_final.svg` (3839 pieces, one contour) | 2469 | 0.9996 |
| `Dragonfly_Wing/Images/cropped_wing_v3.svg` | 4253 | 0.965-1.010 |
| `Insect_Wing_Veins/cropped_wing_opt.svg` (34 contours, 21 open) | 5038 | 0.992-1.038 |
| `old/optimal_leaf.svg` (5 open contours; one falls back) | 2321 | 0.32-1.001 |

For the 1024 x 256 flow tank of the MATLAB starfish example (`--size 0.0803 --center 0.3125,0.125`, ds = 1/2048):
902 points, every chord 1.001 ds except the closing one (0.92). The same outline in the files IB2d ships:
MeshmerizeMe's `star_flow.vertex` (3839 points, chords 0.015-1.51 times their median) and the MATLAB example's
`starfish_flowtank.vertex` (960 points, chords 0.34-1.31 ds). `star_flow.vertex` is exactly the first point of each of
the 3839 path pieces of `starfish_final.svg`, mapped into a 0.5 x 0.5 box with the viewBox's width and height read as
its right and bottom edges (x stretched by 1.45 % against y): the drawing's nodes, not points placed `ds` apart.

Pieces are joined when an end lies within `--merge-tol` (default 1e-5 of the drawing's size) of the next start. An
optimiser that rounds coordinates to three decimals leaves gaps of up to 0.001: with the first default, 1e-6,
`cropped_wing_opt.svg` stayed 240 open pieces (5245 points, chords 0.85-1.16 ds). The script prints a hint when open
contours end close to each other. Elements inside `<defs>`, `<clipPath>`, `<mask>`, `<symbol>`, `<marker>` and
`<pattern>`, and elements with `display="none"`, are not drawn and are skipped.

## Use

```bash
python3 svg_to_vertex.py my_shape.svg --plot
```

```bash
python3 svg_to_vertex.py my_shape.svg --input2d input2d --size 0.1 --center 0.5,0.5
```

Then write the `.target`, `.spring` or `.beam` files for the points by script (chapter 4c), as
`Starfish_Channel/make_starfish_channel.py` does for targets.
