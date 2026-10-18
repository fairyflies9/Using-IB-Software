# Muscle_Models: the muscle laws of chapter 4e, plotted and checked

Chapter 4e of *Using IB Software* (the model gallery and muscle models). Three small scripts, NumPy and Matplotlib
only, no IB2d needed. Each writes its PNGs into the folder you run it from and prints the numbers the chapter quotes
(the PNGs here are those runs).

| file | what |
|---|---|
| `muscle_curves.py` | the length-tension law IB2d uses, `F1 = exp(-((Q-1)/SK)^2)`; Hill's force-velocity law, normalised, and IB2d's `F2` exactly as coded (with `a` in force units); their product; and the crossbridge model of the 2015 lecture (attach at `x = A` at rate `alpha n0 (1 - U)`, detach at rate `beta`, slide at speed `v`): the steady population `u(x)`, the closed-form force `P(v)`, Hill's law with the derived constants, and a numerical integral `n0 * int p u dx` that checks the closed form. Writes `muscle_lt_fv.png` and `muscle_huxley.png`. |
| `activation_wave.py [HeartTube.vertex]` | the heart tube's activation (`give_Traveling_Triggering_Coefficient` from `pyIB2d/Examples/HeartTube_Muscle/give_Muscle_Activation.py`, copied line for line) as a map over the leader points' `x` and time, without the fluid. Writes `activation_wave.png`. |
| `calcium_activation.py` | a calcium model of activation of the kind the activation tutorial describes (Williams et al., lamprey muscle): release from the sarcoplasmic reticulum while a stimulus is on, uptake while it is off, binding to the thin filaments; `Caf` is the activation. One stimulus gives a twitch; trains at 5, 20, 50 and 100 stimuli per second show summation and tetanus. Writes `calcium_activation.png`. **The rate constants are illustrative, not fitted values.** With `--ib2d` it runs IB2d's own version instead, line for line (`Calcium_Dynamics.m` of the MATLAB heart tubes with calcium: forward Euler, `k1, k2, k3, k4 = 9, 50, 40, 19.4` per second, `C = S = 200`, a 5 ms stimulus every 0.5 s for 4 s, uptake always on, unbinding `k4 Caf`) and writes `calcium_ib2d.png`. |

## What they print (October 2026)

- IB2d's `F2` with the heart tube's `a = 0.25`, `b = 4`, `P0 = Fmax = 1e5` is `(4 - 2.5e-6 v)/(v + 4)`: it equals
  `4/(v + 4)` to within a relative `6.25e-7 v` (six digits for `v` up to about 1, four to five at the run's fastest
  muscles, `v` about 85 between dumps); its `Vmax = b P0/a = 1.6e6`. Hill's law with `a/P0 = 0.25`, `b = 4` stalls at
  `v = 16`.
- Crossbridges with `alpha = beta = A = n0 p1 = N = 1`, `gamma = ln 5`: `a = K = 0.5`, `P0 = 2`, `a/P0 = 0.25`,
  `b = 2 N beta/gamma = 1.2427`, `Vmax = 4.9707`; the closed form and the numerical integral agree to `4.5e-8` of `P0`
  at six speeds, and the attached fraction is `alpha/(alpha + beta) = 0.5` at every speed.
- The heart tube (its own `HeartTube.vertex`): tube from `x = 1` to `4`, active region `1.75 .. 3.25`, pulse width
  `0.15`, speed `13.5`, period `0.1`; 7 or 8 of the example's 153 muscles (`HeartTube.muscle`) active at a time (the
  script counts all 155 points of the top row as candidate leaders; the two end points are never in the active region).
- Calcium model with `k1, k2, k3, k4 = 300, 100, 150, 30` per second, `C = 2`, `S = 6`, 5 ms stimuli: a twitch
  peaks at `Caf = 0.53` after 9 ms and halves by 57 ms; over the last 0.1 s of a 0.5 s train, `Caf` runs 0.02-0.54 at
  5 per second, 0.44-0.69 at 20, 0.94-0.96 at 50, and 1.00 at 100.
- IB2d's calcium model (`--ib2d`, `dt = 1e-5` s): each stimulus lifts the free calcium to 5.0; `Caf` peaks at 0.687
  (0.701 from the second stimulus on) about 15 ms after the stimulus starts, halves by 96 ms and is still 0.080 when the
  next stimulus comes, 0.5 s later: separate twitches. (The copy in `128x128_Electromechanical_Pumping_w_Ca_Dynamics`
  still ends with its test plot and `pause()`, so in MATLAB that example stops at the plot until a key is pressed.)

## Run them

```bash
python3 muscle_curves.py
```

```bash
python3 activation_wave.py ../../../../IB2d/pyIB2d/Examples/HeartTube_Muscle/HeartTube.vertex
```

```bash
python3 calcium_activation.py
```

```bash
python3 calcium_activation.py --ib2d
```

(The path in the second command depends on where your IB2d clone is; without it the script builds the example's
tube itself.)

## Sources

The 2015 lecture "Quick introduction to muscle models" and the "Muscle Activation Tutorial" (L. A. Miller); the
2016 talk by N. A. Battista and L. A. Miller; IB2d (https://github.com/nickabattista/IB2d, GPL-3.0; the activation
function in `activation_wave.py` and IB2d's calcium model in `calcium_activation.py --ib2d` are copied from it with
credit). The crossbridge derivation is the 2015 lecture's: A. F. Huxley's (1957) model, simplified to attachment at one
point and detachment at a constant rate (the lecture gives no source for this form; J. Keener and J. Sneyd,
*Mathematical Physiology II*, 2nd ed., chapter 15, is good further reading on muscle). The calcium model's form is from
T. L. Williams, G. Bowtell and N. A. Curtin (1998), as presented in the activation tutorial.
