"""make_input.py: writes input2d.<case> for example IB/13 from <case>_geometry.txt (written by vessel_walls.py),
so that the box, the grid and the inlet band in the input always match the wall points.

    python3 vessel_walls.py --case horse --DT 3e-5 && python3 make_input.py horse  # -> input2d.horse
    python3 vessel_walls.py --case human --DT 5e-5 && python3 make_input.py human  # -> input2d.human

The horse case: inflow on the left face, outflow through the top and bottom faces (the branches), the right face a
wall; the equine pulse. The human case: inflow on the left face, outflow through the right face; a human pulse.
"""
import sys

case = sys.argv[1]
g = {}
for line in open(case + "_geometry.txt"):
    k, v = line.split(" = ", 1)
    g[k.strip()] = v.strip()
LX, LY, NX, NY = float(g["LX"]), float(g["LY"]), int(g["NX"]), int(g["NY"])
Y_LO, Y_HI = float(g["inlet_y_lo"]), float(g["inlet_y_hi"])
D = float(g["D_inlet"])
P = {
    "horse": dict(F=0.6, TP=0.122, K=1.28, U_DIA=10.0, U_SYS=50.0, DT=3.0e-5, outlets="top and bottom",
                  who="a resting horse: 36 beats per minute, the aortic ejection timing of Blissitt & Bonagura (1995), Table 2, as used in the horse aorta study",
                  geom="the silhouette of a horse's carotid artery (Laura Miller's model, used here at its own size: the common carotid is %.2f cm wide in the plane) where the common carotid meets the vessel that runs up to the internal carotid and occipital artery and down to the external carotid; the four branches leave through the top and bottom faces" % D),
    "human": dict(F=1.17, TP=0.10, K=1.28, U_DIA=20.0, U_SYS=70.0, DT=5.0e-5, outlets="right",
                  who="a resting human: 70 beats per minute, peak 0.1 s into the beat",
                  geom="the lumen outline of a human carotid bifurcation (NIH 3D model, used at its own size: the common carotid is %.2f cm wide) in its bifurcation plane; the internal carotid with its bulb and the external carotid leave through the right face" % D),
}[case]
Re_mean = (P["U_DIA"] + (P["U_SYS"] - P["U_DIA"]) * 0.173) * D * 1.05 / 0.035
Re_peak = P["U_SYS"] * D * 1.05 / 0.035
Wo = D / 2 * (2 * 3.14159265 * P["F"] * 1.05 / 0.035) ** 0.5
# The outflow faces carry zero normal traction over their whole width (BANDS = False). Opening only the outlet
# bands (zero traction inside each band, as in IBAMR's IBFE/explicit/ex8, and no-slip elsewhere) was tried first:
# the no-slip strip meets the open band exactly where the leaky target-point wall reaches the face, and the shear
# there blew up (the human case stopped at t = 0.98 s with the time-step abort). The whole face open works; the
# fluid outside the vessel is a dead space that barely moves.
import ast
BANDS = False
outlets = ast.literal_eval(g["outlets"])
def band_expr(face_key, coord, open_val, wall_val):
    """An expression that is open_val inside any outlet band of that face and wall_val elsewhere (BANDS = True),
    or open_val over the whole face."""
    bands = outlets.get(face_key, [])
    if not bands:
        return wall_val
    if not BANDS:
        return open_val
    cond = " || ".join("(%s > %.6f && %s < %.6f)" % (coord, lo, coord, hi) for lo, hi in bands)
    return "(%s) ? %s : %s" % (cond, open_val, wall_val)
# On an outflow face both velocity components get the zero-traction (Neumann) condition: the normal one lets the
# flow leave, the tangential one lets a branch leave at an angle without a shear layer against the face (with the
# tangential velocity pinned to zero, the horse's branches, which meet their faces at 30 and 45 degrees, blew up
# at t = 0.37 s whatever the time step).
u_a = ["1.0"] * 4; u_b = ["0.0"] * 4; v_a = ["1.0"] * 4; v_b = ["0.0"] * 4
if case == "horse":
    # the branches leave through the top (face 3, y_up) and bottom (face 2, y_lo)
    for face, key in ((2, "y<"), (3, "y>")):
        v_a[face] = band_expr(key, "X_0", "0.0", "1.0"); v_b[face] = band_expr(key, "X_0", "1.0", "0.0")
        u_a[face] = band_expr(key, "X_0", "0.0", "1.0"); u_b[face] = band_expr(key, "X_0", "1.0", "0.0")
else:
    # the branches leave through the right face (face 1, x_up)
    u_a[1] = band_expr("x>", "X_1", "0.0", "1.0"); u_b[1] = band_expr("x>", "X_1", "1.0", "0.0")
    v_a[1] = band_expr("x>", "X_1", "0.0", "1.0"); v_b[1] = band_expr("x>", "X_1", "1.0", "0.0")
pulse = "(U_DIA + (U_SYS - U_DIA)*((t - T_CYCLE*rint(t/T_CYCLE - 0.5))/TP)^K*exp(K*(1.0 - (t - T_CYCLE*rint(t/T_CYCLE - 0.5))/TP)))"
g0 = '"(X_1 <= Y_LO) ? 0.0 : ((X_1 >= Y_HI) ? 0.0 : (t < RAMP ? t/RAMP : 1.0)*6.0*%s*(X_1 - Y_LO)*(Y_HI - X_1)/((Y_HI - Y_LO)*(Y_HI - Y_LO)))"' % pulse

text = f"""// IB/13 carotid bifurcation, case "{case}": input file for IBAMR 0.16.0 or newer. Written by make_input.py from
// {case}_geometry.txt; edit that script, or this file, but keep the box and the inlet band equal to the wall points'.
//
// Pulsatile blood flow through {P["geom"]}.
// The walls are target points. The inflow on the left face is a parabola across the lumen whose mean follows a pulse
// U(t) = U_DIA + (U_SYS - U_DIA)*w(t), w(t) = (t/TP)^K*exp(K*(1 - t/TP)) within each cycle ({P["who"]}).
// The outflow faces ({P["outlets"]}) carry zero normal traction. Units: cm, g, s; blood RHO = 1.05, MU = 0.035.
// Reynolds number U*D*RHO/MU about {Re_mean:.0f} at the cycle mean and {Re_peak:.0f} at the systolic peak; Womersley number {Wo:.1f}.
//
// Grid: two levels of refinement ratio 4 on a {NX} x {NY} base: {g["DX"]} cm on the fine level, {D / float(g["DX"]):.0f} cells across the common carotid.
// For the finer (Puma) run: python3 vessel_walls.py --case {case} --fine 2 && python3 make_input.py {case}   (and job.slurm).
// This file must have Unix (LF) line endings.

// constants
PI = 3.14159265358979
// physical parameters
LX = {LX}                                 // box length (cm)
LY = {LY}                                 // box height (cm)
MU = 0.035                                // blood viscosity (g / (cm s))
RHO = 1.05                                // blood density (g / cm^3)
F = {P["F"]}                                   // heart rate (Hz)
T_CYCLE = 1.0/F                           // cardiac period (s)
U_DIA = {P["U_DIA"]}                              // diastolic (baseline) mean inflow velocity (cm / s)
U_SYS = {P["U_SYS"]}                              // peak systolic mean inflow velocity (cm / s)
TP = {P["TP"]}                                // time to peak within the cycle (s)
K = {P["K"]}                                  // pulse shape exponent (w = 0.15 at the end of ejection)
RAMP = 0.2                                // the inflow is ramped up over the first RAMP seconds
Y_LO = {Y_LO:.6f}                           // the inlet lumen on the left face (from {case}_geometry.txt)
Y_HI = {Y_HI:.6f}

// grid spacing parameters
MAX_LEVELS = 2                            // maximum number of levels in locally refined grid
REF_RATIO  = 4                            // refinement ratio between levels
NX = {NX}                                  // coarse cells along x
NY = {NY}                                  // coarse cells along y
NXF = (REF_RATIO^(MAX_LEVELS - 1))*NX     // fine cells along x
NYF = (REF_RATIO^(MAX_LEVELS - 1))*NY     // fine cells along y
DX = (1.0*LX)/NXF                         // fine mesh width (cm)

// solver parameters
DELTA_FUNCTION      = "IB_4"
SOLVER_TYPE         = "STAGGERED"              // the fluid solver to use (STAGGERED or COLLOCATED)
START_TIME          = 0.0e0                    // initial simulation time
END_TIME            = 2.0/F                    // two cycles
GROW_DT             = 2.0e0                    // growth factor for timesteps
NUM_CYCLES          = 1                        // number of cycles of fixed-point iteration
CONVECTIVE_TS_TYPE  = "ADAMS_BASHFORTH"        // convective time stepping type
CONVECTIVE_OP_TYPE  = "PPM"                    // convective differencing discretization type
CONVECTIVE_FORM     = "ADVECTIVE"              // how to compute the convective terms
NORMALIZE_PRESSURE  = FALSE                    // the outflow faces set the pressure level
CFL_MAX             = 0.3                      // maximum CFL number
DT                  = {P["DT"]}                   // maximum timestep size (s); vessel_walls.py --DT sizes the target stiffness for it
ERROR_ON_DT_CHANGE  = TRUE                     // whether to emit an error message if the time step size changes
VORTICITY_TAGGING   = FALSE                    // whether to tag cells for refinement based on vorticity thresholds
TAG_BUFFER          = 1                        // size of tag buffer used by grid generation algorithm
REGRID_CFL_INTERVAL = 0.5                      // regrid whenever any material point could have moved 0.5 meshwidths since previous regrid
OUTPUT_U            = TRUE
OUTPUT_P            = TRUE
OUTPUT_F            = FALSE
OUTPUT_OMEGA        = TRUE
OUTPUT_DIV_U        = TRUE
ENABLE_LOGGING      = TRUE

// output intervals, in time steps: 50 VisIt frames per cycle, and the same number of X/F data files
VIZ_INTERVAL        = int(END_TIME/(100*DT))
DATA_INTERVAL       = int(END_TIME/(100*DT))

// collocated solver parameters
PROJECTION_METHOD_TYPE = "PRESSURE_UPDATE"
SECOND_ORDER_PRESSURE_UPDATE = TRUE

VelocityInitialConditions {{
   function_0 = "0.0"                     // initial  conditions for the x-component of the velocity
   function_1 = "0.0"                     // initial  conditions for the y-component of the velocity
}}

IBHierarchyIntegrator {{
   start_time          = START_TIME
   end_time            = END_TIME
   grow_dt             = GROW_DT
   num_cycles          = NUM_CYCLES
   regrid_cfl_interval = REGRID_CFL_INTERVAL
   dt_max              = DT
   error_on_dt_change  = ERROR_ON_DT_CHANGE
   tag_buffer          = TAG_BUFFER
   enable_logging      = ENABLE_LOGGING
}}

IBMethod {{
   delta_fcn      = DELTA_FUNCTION
   enable_logging = ENABLE_LOGGING
}}

IBStandardInitializer {{
   max_levels = MAX_LEVELS
   structure_names = "{case}"
   {case} {{
      level_number = MAX_LEVELS - 1
   }}
}}

INSCollocatedHierarchyIntegrator {{
   mu                            = MU
   rho                           = RHO
   start_time                    = START_TIME
   end_time                      = END_TIME
   grow_dt                       = GROW_DT
   convective_time_stepping_type = CONVECTIVE_TS_TYPE
   convective_op_type            = CONVECTIVE_OP_TYPE
   convective_difference_form    = CONVECTIVE_FORM
   normalize_pressure            = NORMALIZE_PRESSURE
   cfl                           = CFL_MAX
   dt_max                        = DT
   using_vorticity_tagging       = VORTICITY_TAGGING
   vorticity_rel_thresh          = 0.25,0.125
   tag_buffer                    = TAG_BUFFER
   output_U                      = OUTPUT_U
   output_P                      = OUTPUT_P
   output_F                      = OUTPUT_F
   output_Omega                  = OUTPUT_OMEGA
   output_Div_U                  = OUTPUT_DIV_U
   enable_logging                = ENABLE_LOGGING
   projection_method_type        = PROJECTION_METHOD_TYPE
   use_2nd_order_pressure_update = SECOND_ORDER_PRESSURE_UPDATE
}}

INSStaggeredHierarchyIntegrator {{
   mu                            = MU
   rho                           = RHO
   start_time                    = START_TIME
   end_time                      = END_TIME
   grow_dt                       = GROW_DT
   convective_time_stepping_type = CONVECTIVE_TS_TYPE
   convective_op_type            = CONVECTIVE_OP_TYPE
   convective_difference_form    = CONVECTIVE_FORM
   normalize_pressure            = NORMALIZE_PRESSURE
   cfl                           = CFL_MAX
   dt_max                        = DT
   using_vorticity_tagging       = VORTICITY_TAGGING
   vorticity_rel_thresh          = 0.25,0.125
   tag_buffer                    = TAG_BUFFER
   output_U                      = OUTPUT_U
   output_P                      = OUTPUT_P
   output_F                      = OUTPUT_F
   output_Omega                  = OUTPUT_OMEGA
   output_Div_U                  = OUTPUT_DIV_U
   enable_logging                = ENABLE_LOGGING
}}

Main {{
   solver_type = SOLVER_TYPE
   log_file_name               = "IB2d.log"
   log_all_nodes               = FALSE
   viz_writer                  = "VisIt","Silo"
   viz_dump_interval           = VIZ_INTERVAL
   viz_dump_dirname            = "viz_IB2d"
   visit_number_procs_per_file = 1
   restart_dump_interval       = 0
   restart_dump_dirname        = "restart_IB2d"
   data_dump_interval          = DATA_INTERVAL
   data_dump_dirname           = "hier_data_IB2d"
   timer_dump_interval         = 0
}}

CartesianGeometry {{
   domain_boxes = [ (0,0) , (NX - 1,NY - 1) ]
   x_lo = 0.0, 0.0        // lower end of computational domain.
   x_up = LX, LY          // upper end of computational domain.
   periodic_dimension = 0,0
}}

GriddingAlgorithm {{
   max_levels = MAX_LEVELS
   ratio_to_coarser {{
      level_1 = REF_RATIO,REF_RATIO
      level_2 = REF_RATIO,REF_RATIO
      level_3 = REF_RATIO,REF_RATIO
   }}
   largest_patch_size {{
      level_0 = 512, 512  // all finer levels will use same values as level_0
   }}
   smallest_patch_size {{
      level_0 =   8,  8  // all finer levels will use same values as level_0
   }}
   efficiency_tolerance = 0.85e0  // min % of tag cells in new patch level
   combine_efficiency   = 0.85e0  // chop box if sum of volumes of smaller boxes < efficiency * vol of large box
}}

StandardTagAndInitialize {{
   tagging_method = "GRADIENT_DETECTOR"
}}

LoadBalancer {{
   bin_pack_method     = "SPATIAL"
   max_workload_factor = 1
}}

TimerManager{{
   print_exclusive = FALSE
   print_total     = TRUE
   print_threshold = 0.1
   timer_list      = "IBAMR::*::*","IBTK::*::*","*::*::*"
}}

// Boundary conditions. Faces: 0 = x_lo (the inlet), 1 = x_up, 2 = y_lo, 3 = y_up; the outflow faces are {P["outlets"]}.
// a*u + b*(du/dn) = g: a = 1, b = 0 sets the velocity; a = 0, b = 1 sets the normal traction (zero here).
VelocityBcCoefs_0 {{
   PI = 3.141592653589793
   T_CYCLE = T_CYCLE
   U_DIA = U_DIA
   U_SYS = U_SYS
   TP = TP
   K = K
   RAMP = RAMP
   Y_LO = Y_LO
   Y_HI = Y_HI

   acoef_function_0 = "{u_a[0]}"
   acoef_function_1 = "{u_a[1]}"
   acoef_function_2 = "{u_a[2]}"
   acoef_function_3 = "{u_a[3]}"

   bcoef_function_0 = "{u_b[0]}"
   bcoef_function_1 = "{u_b[1]}"
   bcoef_function_2 = "{u_b[2]}"
   bcoef_function_3 = "{u_b[3]}"

   // the inlet: a parabola across the lumen [Y_LO, Y_HI] whose mean is the pulse U(t), ramped up over RAMP s;
   // t - T_CYCLE*rint(t/T_CYCLE - 0.5) is the time within the cycle (muParser has rint but no floor, and ^ but no pow)
   gcoef_function_0 = {g0}
   gcoef_function_1 = "0.0"
   gcoef_function_2 = "0.0"
   gcoef_function_3 = "0.0"
}}

VelocityBcCoefs_1 {{
   acoef_function_0 = "{v_a[0]}"
   acoef_function_1 = "{v_a[1]}"
   acoef_function_2 = "{v_a[2]}"
   acoef_function_3 = "{v_a[3]}"

   bcoef_function_0 = "{v_b[0]}"
   bcoef_function_1 = "{v_b[1]}"
   bcoef_function_2 = "{v_b[2]}"
   bcoef_function_3 = "{v_b[3]}"

   gcoef_function_0 = "0.0"
   gcoef_function_1 = "0.0"
   gcoef_function_2 = "0.0"
   gcoef_function_3 = "0.0"
}}
"""
open("input2d." + case, "w", newline="\n").write(text)
print("wrote input2d.%s: box %g x %g, grid %d x %d (fine %s cm), inlet %.3f-%.3f, DT %g, Re %.0f/%.0f, Wo %.1f" % (case, LX, LY, NX, NY, g["DX"], Y_LO, Y_HI, P["DT"], Re_mean, Re_peak, Wo))
