# Analysis report: <study name>

A condensed version of the protocol with the results so far (chapter 29, after Lindsay Waldrop's VisIt guide): what
you would write in the Methods section of a paper, erring on the side of more detail, and an excellent first draft of
it.

## What was done, and where

A paragraph per measurement: the box, point or line (coordinates), the query, frame by frame or through time, and the
check made on it. Point to the protocol for the steps.

## Results

The numbers, with their spread, and any statistics so far.

## Figures

Each graph or picture with a full caption: what is plotted, from which run and frame, with which settings.

## Notes

Rough notes on anything interesting or puzzling in the results, and on runs that exist but were not used (and why).

---

## Example (IB/11, chapter 29)

The net flow round the loop was measured as the flow rate per unit depth across six lines (the top straight at x = 0,
both bends at y = 0, and the elastic section at x = 0.15 between the walls' rest positions and at x = ±0.15 across the
whole pericardium), integrating the velocity across each line from 50-sample (51-point) lineouts in every frame (VisIt 3.5.0,
`visit_queries.py`). Both suction modes turn the loop clockwise: 1.58e-3 m²/s over two periods for `TARGET_VP` and
6.69e-4 m²/s for `FORCE_VP`, equal to within 0.3 % on the top straight and both bends. The line between the walls' rest
positions misses the moving tube (1.2e-3 and 2.5e-4 m²/s). Note: the `FORCE_VP` markers drift +2.1 cm in two periods,
against the flow (the fluid moved −1.3 cm along the elastic section): a marker drift is not a flow rate.
