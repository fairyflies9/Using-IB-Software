# Data sheet: <run folder name>

One per simulation folder, kept in the folder (chapter 29, after Lindsay Waldrop's VisIt guide), so that whoever comes
behind you, or you in a few years, does not have to find the parameters in the code or remember when it ran.

| | |
|---|---|
| study | |
| run name (folder) | |
| what varies in this run | (the parameter of the sweep and its value) |
| date run, by whom | |
| machine, cores, wall time | |
| code (IBAMR / IB2d version, example, commit) | |
| input file (name; or copied below) | |
| structure files | |
| grid (levels, finest Δx), Δt, end time | |
| fluid (ρ, μ) and dimensionless numbers (Re, Wo, ...) | |
| output (frames, interval, folders) | |
| how it ended (normal, stopped at t = ..., error message) | |
| used in (analysis report, figure, paper) | |
| notes | |

---

## Example (IB/11 `TARGET_VP`, chapter 29)

| | |
|---|---|
| study | the heart-tube pump of chapter 9b: five ways to drive it |
| run name (folder) | `TARGET_VP` |
| what varies in this run | the actuation: target points moved in and out (suction) |
| date run, by whom | 13 October 2026, for this tutorial |
| machine, cores, wall time | a desktop PC (Intel i9-12900KF; WSL2, Ubuntu 24.04), 3 cores (`mpirun -np 3`); 68 min, 07:52 to 09:01, with the other four modes running at the same time |
| code | IBAMR 0.19.0, `examples/IB/11-heart-tube-pump`, input `input2d` as shipped |
| input file | `input2d` as shipped (`ACTUATION = "TARGET_VP"`) |
| structure files | `actuator_top_512`, `actuator_bot_512` (`.vertex`, `.target`); `heart_tube_512` (`.vertex`, `.spring`, `.beam`, `.target`); `heart_peri_512`, `heart_race_512` (`.vertex`, `.target`); `markers_512.vertex` |
| grid, Δt, end time | 4 levels, ratio 4, finest Δx = 1/512 m; Δt = 5e-5 s; 2 s (40,000 steps) |
| fluid | ρ = 1000 kg/m³, μ = 0.157 N s/m² (Wo = 10 at 1 Hz) |
| output | 51 frames (every 800 steps) in `viz_IB2d`, positions in `hier_data_IB2d` |
| how it ended | normally, at t = 2 s |
| used in | chapter 9b (squeeze, markers), chapter 29 (flow rate) |
| notes | the 121 markers are passive points (11 × 11: x from −0.2 to 0.2, y from −0.20 to −0.10), 22 of them on the walls' rest positions |
