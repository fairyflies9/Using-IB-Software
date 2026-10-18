// Copyright (c) 2002-2014, Boyce Griffith
// All rights reserved.
//
// Redistribution and use in source and binary forms, with or without
// modification, are permitted provided that the following conditions are met:
//
//    * Redistributions of source code must retain the above copyright notice,
//      this list of conditions and the following disclaimer.
//
//    * Redistributions in binary form must reproduce the above copyright
//      notice, this list of conditions and the following disclaimer in the
//      documentation and/or other materials provided with the distribution.
//
//    * Neither the name of New York University nor the names of its
//      contributors may be used to endorse or promote products derived from
//      this software without specific prior written permission.
//
// THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
// AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
// IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
// ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
// LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
// CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
// SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
// INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
// CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
// ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
// POSSIBILITY OF SUCH DAMAGE.
//
// Course example from the UNC IBFE tutorials (2017-2018) and the University of
// Arizona versions (2020-2024), revised for the "Using IB Software" tutorials
// as example IBFE/10.
//
// A thin elastic plate (a gmsh tetrahedral mesh, 0.125 by 2 by 2) sits across
// the flow in a 3D flow tank. A band across the middle of the plate is held in
// place by a tether (target) force; the rest of the plate is free to bend.
//
// Changes from the 2020-2024 course version:
//   * IBTKInit starts and stops MPI, PETSc, libMesh and SAMRAI.
//   * The deprecated IBAMR_config.h and IBTK_config.h includes are removed.
//   * libMesh::Order replaces the old libMeshEnums::Order, IBTK::rel_equal_eps
//     and IBTK_MPI replace MathUtilities and SAMRAI_MPI, and the ExodusII
//     writer is made with std::make_unique.
//   * output_data() did nothing (its body was commented out) but was called
//     every time step (data_dump_interval = 1). It now computes the total
//     tether force on the plate, prints it, and writes it to a text file.
//   * "Max Jacobian" and "Min Jacobian" were printed every step but were
//     always 1, because nothing updated them. The stress function now records
//     the range of J = det(FF), which is printed with the tether force.
//   * std::abs replaces abs on a double; the unused s_dump, dx and ds are
//     removed; the comment "x is actual position" now names X.
//   * Options from the 2017 version are back as input keys: TRANSLATE_X moves
//     the plate (and its tether) along x, and TWO_MATERIALS gives the plate a
//     stiffer "stem" band and softer "leaf" parts. The tether band width is
//     TETHER_HALF_WIDTH. The defaults give the course version's plate.
//   * Restarted runs save and reload the plate's finite element data and
//     append to the ExodusII file, as in IBAMR's own examples. Unlike those
//     examples, only processor 0 reopens the ExodusII file; otherwise a
//     restart on more than one process leaves a file that cannot be read.
// Tested with IBAMR 0.16.0 and 0.19.0.

// Config files
#include <SAMRAI_config.h>

// Headers for basic PETSc functions
#include <petscsys.h>

// Headers for basic SAMRAI objects
#include <BergerRigoutsos.h>
#include <CartesianGridGeometry.h>
#include <LoadBalancer.h>
#include <StandardTagAndInitialize.h>

// Headers for basic libMesh objects
#include <libmesh/boundary_info.h>
#include <libmesh/dof_map.h>
#include <libmesh/equation_systems.h>
#include <libmesh/exodusII_io.h>
#include <libmesh/fe.h>
#include <libmesh/mesh.h>
#include <libmesh/quadrature.h>

// Headers for application-specific algorithm/data structure objects
#include <ibamr/IBExplicitHierarchyIntegrator.h>
#include <ibamr/IBFEMethod.h>
#include <ibamr/INSCollocatedHierarchyIntegrator.h>
#include <ibamr/INSStaggeredHierarchyIntegrator.h>

#include <ibtk/AppInitializer.h>
#include <ibtk/IBTKInit.h>
#include <ibtk/IBTK_MPI.h>
#include <ibtk/libmesh_utilities.h>
#include <ibtk/muParserCartGridFunction.h>
#include <ibtk/muParserRobinBcCoefs.h>

#include <boost/multi_array.hpp>

#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <memory>
#include <string>
#include <vector>

// Set up application namespace declarations
#include <ibamr/app_namespaces.h>

// Elasticity model data.
namespace ModelData
{
// Material parameters of the plate, a compressible neo-Hookean solid: shear
// modulus mu and first Lame parameter beta, for the "stem" and the "leaf".
// These values are overwritten by MU_STEM, BETA_STEM, MU_LEAF and BETA_LEAF
// from input3d before the first time step.
static double mu_stem = 1.0e-2;
static double mu_leaf = 1.0e2;
static double beta_stem = 1.0e3;
static double beta_leaf = 1.0e3;

// With two_materials = false (the default) the whole plate is stem material.
// With two_materials = true, points with |s(2)| < stem_half_width are stem
// and the rest is leaf, as in the 2017 version.
static bool two_materials = false;
static double stem_half_width = 0.25;

// Tether: the points with |s(2)| < tether_half_width are pulled toward their
// starting positions with stiffness kappa_s (input keys KAPPA_S and
// TETHER_HALF_WIDTH).
static double kappa_s = 1.0e5;
static double tether_half_width = 0.1;

// Distance the plate and its tether are moved along x at the start of the
// run (input key TRANSLATE_X). The 2017 version used -7, in a tank that ran
// from x = -16 to 16.
static double translate_x = 0.0;

// Smallest and largest J = det(FF) seen by the stress function since they
// were last printed (see output_data()).
static double J_minimum = std::numeric_limits<double>::max();
static double J_maximum = -std::numeric_limits<double>::max();

// Initial coordinate mapping: where each point of the mesh starts. s is the
// position in the mesh file and X is the starting position in the fluid.
void
coordinate_mapping_function(libMesh::Point& X, const libMesh::Point& s, void* /*ctx*/)
{
    X(0) = s(0) + translate_x;
    X(1) = s(1);
    X(2) = s(2);
    return;
} // coordinate_mapping_function

// Target ("tether") force on the plate, per unit reference volume.
//   s is the reference position of a point of the plate (its position in the
//     mesh file): s(0), s(1) and s(2) are its x, y and z coordinates.
//   X is where that point is now.
// Only the band |s(2)| < tether_half_width across the middle of the plate is
// tethered. It is pulled toward its starting position, s moved by translate_x.
void
target_force_function(VectorValue<double>& F,
                      const TensorValue<double>& /*FF*/,
                      const libMesh::Point& X,
                      const libMesh::Point& s,
                      Elem* const /*elem*/,
                      const std::vector<const std::vector<double>*>& /*var_data*/,
                      const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                      double /*time*/,
                      void* /*ctx*/)
{
    // apply tether force only if z-coordinate of original position is within tether_half_width of center.
    double kappa = 0.0; // no tether force outside the band
    if (std::abs(s(2)) < tether_half_width) kappa = kappa_s;

    libMesh::Point s_target = s; // the tether location...
    s_target(0) += translate_x;  // ...after the translation (none by default)

    F = kappa * (s_target - X); // Note X is the actual position, s_target is the desired position
    return;
} // target_force_function

// Stress tensor functions. The first Piola-Kirchhoff stress of the
// compressible neo-Hookean material is split into two parts. The deviatoric
// part is mu*FF. The dilational part, (-mu + beta*log(J))*FF^{-T} with
// J = det(FF), makes the undeformed plate stress-free (at FF = I the two
// parts cancel) and resists changes in volume.
void
PK1_dev_stress_function(TensorValue<double>& PP,
                        const TensorValue<double>& FF,
                        const libMesh::Point& /*X*/,
                        const libMesh::Point& s,
                        Elem* const /*elem*/,
                        const std::vector<const std::vector<double>*>& /*var_data*/,
                        const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                        double /*time*/,
                        void* /*ctx*/)
{
    const bool leaf = two_materials && std::abs(s(2)) >= stem_half_width;
    const double mu = leaf ? mu_leaf : mu_stem;
    PP = mu * FF;
    return;
} // PK1_dev_stress_function

void
PK1_dil_stress_function(TensorValue<double>& PP,
                        const TensorValue<double>& FF,
                        const libMesh::Point& /*X*/,
                        const libMesh::Point& s,
                        Elem* const /*elem*/,
                        const std::vector<const std::vector<double>*>& /*var_data*/,
                        const std::vector<const std::vector<VectorValue<double> >*>& /*grad_var_data*/,
                        double /*time*/,
                        void* /*ctx*/)
{
    const bool leaf = two_materials && std::abs(s(2)) >= stem_half_width;
    const double mu = leaf ? mu_leaf : mu_stem;
    const double beta = leaf ? beta_leaf : beta_stem;
    const double J = FF.det();
    J_minimum = std::min(J_minimum, J);
    J_maximum = std::max(J_maximum, J);
    PP = (-1.0 * mu + beta * std::log(J)) * tensor_inverse_transpose(FF, NDIM);
    return;
} // PK1_dil_stress_function
} // namespace ModelData
using namespace ModelData;

// Function prototypes
void output_data(Pointer<PatchHierarchy<NDIM> > patch_hierarchy,
                 Pointer<INSHierarchyIntegrator> navier_stokes_integrator,
                 Mesh& mesh,
                 EquationSystems* equation_systems,
                 const std::string& coords_system_name,
                 const int iteration_num,
                 const double loop_time,
                 const string& data_dump_dirname);

/*******************************************************************************
 * For each run, the input filename and restart information (if needed) must   *
 * be given on the command line.  For non-restarted case, command line is:     *
 *                                                                             *
 *    executable <input file name>                                             *
 *                                                                             *
 * For restarted run, command line is:                                         *
 *                                                                             *
 *    executable <input file name> <restart directory> <restart number>        *
 *                                                                             *
 *******************************************************************************/
int
main(int argc, char* argv[])
{
    // Initialize MPI, PETSc, libMesh, SAMRAI and IBAMR. IBTKInit also shuts
    // them down when it goes out of scope at the end of main().
    IBTKInit ibtk_init(argc, argv, MPI_COMM_WORLD);
    const LibMeshInit& init = ibtk_init.getLibMeshInit();

    { // cleanup dynamically allocated objects prior to shutdown

        // Parse command line options, set some standard options from the input
        // file, initialize the restart database (if this is a restarted run),
        // and enable file logging.
        Pointer<AppInitializer> app_initializer = new AppInitializer(argc, argv, "IB.log");
        Pointer<Database> input_db = app_initializer->getInputDatabase();

        // Get various standard options set in the input file.
        const bool dump_viz_data = app_initializer->dumpVizData();
        const int viz_dump_interval = app_initializer->getVizDumpInterval();
        const bool uses_visit = dump_viz_data && app_initializer->getVisItDataWriter();
        const bool uses_exodus = dump_viz_data && !app_initializer->getExodusIIFilename().empty();
        const string exodus_filename = app_initializer->getExodusIIFilename();

        const bool dump_restart_data = app_initializer->dumpRestartData();
        const int restart_dump_interval = app_initializer->getRestartDumpInterval();
        const string restart_dump_dirname = app_initializer->getRestartDumpDirectory();
        const string restart_read_dirname = app_initializer->getRestartReadDirectory();
        const int restart_restore_num = app_initializer->getRestartRestoreNumber();

        const bool dump_postproc_data = app_initializer->dumpPostProcessingData();
        const int postproc_data_dump_interval = app_initializer->getPostProcessingDataDumpInterval();
        const string postproc_data_dump_dirname = app_initializer->getPostProcessingDataDumpDirectory();
        if (dump_postproc_data && (postproc_data_dump_interval > 0) && !postproc_data_dump_dirname.empty())
        {
            Utilities::recursiveMkdir(postproc_data_dump_dirname);
        }

        const bool dump_timer_data = app_initializer->dumpTimerData();
        const int timer_dump_interval = app_initializer->getTimerDumpInterval();

        // Model parameters from the input file.
        // (ModelData:: is written out because another "mu" is also visible here.)
        ModelData::mu_leaf = input_db->getDouble("MU_LEAF");
        ModelData::mu_stem = input_db->getDouble("MU_STEM");
        ModelData::beta_stem = input_db->getDouble("BETA_STEM");
        ModelData::beta_leaf = input_db->getDouble("BETA_LEAF");
        ModelData::kappa_s = input_db->getDouble("KAPPA_S");
        ModelData::two_materials = input_db->getBoolWithDefault("TWO_MATERIALS", false);
        ModelData::stem_half_width = input_db->getDoubleWithDefault("STEM_HALF_WIDTH", ModelData::stem_half_width);
        ModelData::tether_half_width =
            input_db->getDoubleWithDefault("TETHER_HALF_WIDTH", ModelData::tether_half_width);
        ModelData::translate_x = input_db->getDoubleWithDefault("TRANSLATE_X", 0.0);

        // Read the finite element mesh of the plate: a gmsh file in MSH 2.2
        // ASCII format (see README.md for how it was made).
        Mesh mesh(init.comm(), NDIM);
        const string mesh_filename = input_db->getStringWithDefault("MESH_FILENAME", "plate2.msh");
        mesh.read(mesh_filename);
        mesh.prepare_for_use();

        // Create major algorithm and data objects that comprise the
        // application.  These objects are configured from the input database
        // and, if this is a restarted run, from the restart database.
        Pointer<INSHierarchyIntegrator> navier_stokes_integrator;
        const string solver_type = app_initializer->getComponentDatabase("Main")->getString("solver_type");
        if (solver_type == "STAGGERED")
        {
            navier_stokes_integrator = new INSStaggeredHierarchyIntegrator(
                "INSStaggeredHierarchyIntegrator",
                app_initializer->getComponentDatabase("INSStaggeredHierarchyIntegrator"));
        }
        else if (solver_type == "COLLOCATED")
        {
            navier_stokes_integrator = new INSCollocatedHierarchyIntegrator(
                "INSCollocatedHierarchyIntegrator",
                app_initializer->getComponentDatabase("INSCollocatedHierarchyIntegrator"));
        }
        else
        {
            TBOX_ERROR("Unsupported solver type: " << solver_type << "\n"
                                                   << "Valid options are: COLLOCATED, STAGGERED");
        }
        Pointer<IBFEMethod> ib_method_ops =
            new IBFEMethod("IBFEMethod",
                           app_initializer->getComponentDatabase("IBFEMethod"),
                           &mesh,
                           app_initializer->getComponentDatabase("GriddingAlgorithm")->getInteger("max_levels"),
                           /*register_for_restart*/ true,
                           restart_read_dirname,
                           restart_restore_num);
        Pointer<IBHierarchyIntegrator> time_integrator =
            new IBExplicitHierarchyIntegrator("IBHierarchyIntegrator",
                                              app_initializer->getComponentDatabase("IBHierarchyIntegrator"),
                                              ib_method_ops,
                                              navier_stokes_integrator);
        Pointer<CartesianGridGeometry<NDIM> > grid_geometry = new CartesianGridGeometry<NDIM>(
            "CartesianGeometry", app_initializer->getComponentDatabase("CartesianGeometry"));
        Pointer<PatchHierarchy<NDIM> > patch_hierarchy = new PatchHierarchy<NDIM>("PatchHierarchy", grid_geometry);
        Pointer<StandardTagAndInitialize<NDIM> > error_detector =
            new StandardTagAndInitialize<NDIM>("StandardTagAndInitialize",
                                               time_integrator,
                                               app_initializer->getComponentDatabase("StandardTagAndInitialize"));
        Pointer<BergerRigoutsos<NDIM> > box_generator = new BergerRigoutsos<NDIM>();
        Pointer<LoadBalancer<NDIM> > load_balancer =
            new LoadBalancer<NDIM>("LoadBalancer", app_initializer->getComponentDatabase("LoadBalancer"));
        Pointer<GriddingAlgorithm<NDIM> > gridding_algorithm =
            new GriddingAlgorithm<NDIM>("GriddingAlgorithm",
                                        app_initializer->getComponentDatabase("GriddingAlgorithm"),
                                        error_detector,
                                        box_generator,
                                        load_balancer);

        // Configure the IBFE solver: register the stress and force functions
        // (and the coordinate mapping when the plate is moved), then set up
        // the finite element systems.
        IBFEMethod::PK1StressFcnData PK1_dev_stress_data(PK1_dev_stress_function);
        IBFEMethod::PK1StressFcnData PK1_dil_stress_data(PK1_dil_stress_function);
        IBFEMethod::LagBodyForceFcnData target_force_data(target_force_function);
        PK1_dev_stress_data.quad_order =
            Utility::string_to_enum<libMesh::Order>(input_db->getStringWithDefault("PK1_DEV_QUAD_ORDER", "SEVENTH"));
        PK1_dil_stress_data.quad_order =
            Utility::string_to_enum<libMesh::Order>(input_db->getStringWithDefault("PK1_DIL_QUAD_ORDER", "SEVENTH"));
        ib_method_ops->registerPK1StressFunction(PK1_dev_stress_data);
        ib_method_ops->registerPK1StressFunction(PK1_dil_stress_data);
        ib_method_ops->registerLagBodyForceFunction(target_force_data);
        if (ModelData::translate_x != 0.0)
        {
            ib_method_ops->registerInitialCoordinateMappingFunction(coordinate_mapping_function);
        }
        ib_method_ops->initializeFEEquationSystems();
        EquationSystems* equation_systems = ib_method_ops->getFEDataManager()->getEquationSystems();

        // Create Eulerian initial condition specification objects.
        if (input_db->keyExists("VelocityInitialConditions"))
        {
            Pointer<CartGridFunction> u_init = new muParserCartGridFunction(
                "u_init", app_initializer->getComponentDatabase("VelocityInitialConditions"), grid_geometry);
            navier_stokes_integrator->registerVelocityInitialConditions(u_init);
        }

        if (input_db->keyExists("PressureInitialConditions"))
        {
            Pointer<CartGridFunction> p_init = new muParserCartGridFunction(
                "p_init", app_initializer->getComponentDatabase("PressureInitialConditions"), grid_geometry);
            navier_stokes_integrator->registerPressureInitialConditions(p_init);
        }

        // Create Eulerian boundary condition specification objects (when necessary).
        const IntVector<NDIM>& periodic_shift = grid_geometry->getPeriodicShift();
        vector<RobinBcCoefStrategy<NDIM>*> u_bc_coefs(NDIM);
        if (periodic_shift.min() > 0)
        {
            for (unsigned int d = 0; d < NDIM; ++d)
            {
                u_bc_coefs[d] = nullptr;
            }
        }
        else
        {
            for (unsigned int d = 0; d < NDIM; ++d)
            {
                ostringstream bc_coefs_name_stream;
                bc_coefs_name_stream << "u_bc_coefs_" << d;
                const string bc_coefs_name = bc_coefs_name_stream.str();

                ostringstream bc_coefs_db_name_stream;
                bc_coefs_db_name_stream << "VelocityBcCoefs_" << d;
                const string bc_coefs_db_name = bc_coefs_db_name_stream.str();

                u_bc_coefs[d] = new muParserRobinBcCoefs(
                    bc_coefs_name, app_initializer->getComponentDatabase(bc_coefs_db_name), grid_geometry);
            }
            navier_stokes_integrator->registerPhysicalBoundaryConditions(u_bc_coefs);
        }

        // Create Eulerian body force function specification objects.
        if (input_db->keyExists("ForcingFunction"))
        {
            Pointer<CartGridFunction> f_fcn = new muParserCartGridFunction(
                "f_fcn", app_initializer->getComponentDatabase("ForcingFunction"), grid_geometry);
            time_integrator->registerBodyForceFunction(f_fcn);
        }

        // Set up visualization plot file writers.
        Pointer<VisItDataWriter<NDIM> > visit_data_writer = app_initializer->getVisItDataWriter();
        if (uses_visit)
        {
            time_integrator->registerVisItDataWriter(visit_data_writer);
        }
        std::unique_ptr<ExodusII_IO> exodus_io = uses_exodus ? std::make_unique<ExodusII_IO>(mesh) : nullptr;

        // A restarted run adds its time steps to the existing ExodusII file.
        // Only processor 0 writes the file, so only processor 0 reopens it:
        // libMesh 1.7.8 reopens it on every processor when told to append,
        // and with more than one process the file is then damaged (it can no
        // longer be read).
        if (uses_exodus)
        {
            const bool from_restart = RestartManager::getManager()->isFromRestart();
            exodus_io->append(from_restart && IBTK_MPI::getRank() == 0);
        }

        // Initialize hierarchy configuration and data on all patches.
        ib_method_ops->initializeFEData();
        time_integrator->initializePatchHierarchy(patch_hierarchy, gridding_algorithm);

        // Deallocate initialization objects.
        app_initializer.setNull();

        // Print the input database contents to the log file.
        plog << "Input database:\n";
        input_db->printClassData(plog);

        // Write out initial visualization data.
        int iteration_num = time_integrator->getIntegratorStep();
        double loop_time = time_integrator->getIntegratorTime();
        if (dump_viz_data)
        {
            pout << "\n\nWriting visualization files...\n\n";
            if (uses_visit)
            {
                time_integrator->setupPlotData();
                visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
            }
            if (uses_exodus)
            {
                exodus_io->write_timestep(
                    exodus_filename, *equation_systems, iteration_num / viz_dump_interval + 1, loop_time);
            }
        }

        // Main time step loop.
        double loop_time_end = time_integrator->getEndTime();
        double dt = 0.0;
        while (!IBTK::rel_equal_eps(loop_time, loop_time_end) && time_integrator->stepsRemaining())
        {
            iteration_num = time_integrator->getIntegratorStep();
            loop_time = time_integrator->getIntegratorTime();

            pout << "\n";
            pout << "+++++++++++++++++++++++++++++++++++++++++++++++++++\n";
            pout << "At beginning of timestep # " << iteration_num << "\n";
            pout << "Simulation time is " << loop_time << "\n";

            dt = time_integrator->getMaximumTimeStepSize();
            time_integrator->advanceHierarchy(dt);
            loop_time += dt;

            pout << "\n";
            pout << "At end       of timestep # " << iteration_num << "\n";
            pout << "Simulation time is " << loop_time << "\n";
            pout << "+++++++++++++++++++++++++++++++++++++++++++++++++++\n";
            pout << "\n";

            // At specified intervals, write visualization and restart files,
            // print out timer data, and store hierarchy data for post
            // processing.
            iteration_num += 1;
            const bool last_step = !time_integrator->stepsRemaining();
            if (dump_viz_data && (iteration_num % viz_dump_interval == 0 || last_step))
            {
                pout << "\nWriting visualization files...\n\n";
                if (uses_visit)
                {
                    time_integrator->setupPlotData();
                    visit_data_writer->writePlotData(patch_hierarchy, iteration_num, loop_time);
                }
                if (uses_exodus)
                {
                    exodus_io->write_timestep(
                        exodus_filename, *equation_systems, iteration_num / viz_dump_interval + 1, loop_time);
                }
            }
            if (dump_restart_data && (iteration_num % restart_dump_interval == 0 || last_step))
            {
                pout << "\nWriting restart files...\n\n";
                RestartManager::getManager()->writeRestartFile(restart_dump_dirname, iteration_num);
                ib_method_ops->writeFEDataToRestartFile(restart_dump_dirname, iteration_num);
            }
            if (dump_timer_data && (iteration_num % timer_dump_interval == 0 || last_step))
            {
                pout << "\nWriting timer data...\n\n";
                TimerManager::getManager()->print(plog);
            }
            if (dump_postproc_data && (iteration_num % postproc_data_dump_interval == 0 || last_step))
            {
                output_data(patch_hierarchy,
                            navier_stokes_integrator,
                            mesh,
                            equation_systems,
                            ib_method_ops->getCurrentCoordinatesSystemName(),
                            iteration_num,
                            loop_time,
                            postproc_data_dump_dirname);
            }
        }

        // Cleanup Eulerian boundary condition specification objects (when
        // necessary).
        for (unsigned int d = 0; d < NDIM; ++d) delete u_bc_coefs[d];

    } // cleanup dynamically allocated objects prior to shutdown
    return 0;
} // main

// Compute the total tether force on the plate, the integral of
// target_force_function() over the plate, and print it with the range of
// J = det(FF) since the last call. The force is also appended to the file
// tether_force.txt in data_dump_dirname (columns: time, Fx, Fy, Fz). Turned on
// by data_dump_interval > 0 in the Main block of input3d.
//
// The tether is what holds the plate against the flow, so (once the plate has
// stopped bending) the tether force is minus the force of the flow on the
// plate: Fx is minus the drag.
void
output_data(Pointer<PatchHierarchy<NDIM> > /*patch_hierarchy*/,
            Pointer<INSHierarchyIntegrator> /*navier_stokes_integrator*/,
            Mesh& mesh,
            EquationSystems* equation_systems,
            const std::string& coords_system_name,
            const int iteration_num,
            const double loop_time,
            const string& data_dump_dirname)
{
    plog << "computing the tether force at iteration " << iteration_num << endl;
    plog << "simulation time is " << loop_time << endl;

    // The current positions X of the mesh nodes.
    const unsigned int dim = mesh.mesh_dimension();
    System& X_system = equation_systems->get_system(coords_system_name);
    NumericVector<double>* X_vec = X_system.solution.get();
    NumericVector<double>* X_ghost_vec = X_system.current_local_solution.get();
    copy_and_synch(*X_vec, *X_ghost_vec);
    const DofMap& dof_map = X_system.get_dof_map();
    std::vector<std::vector<unsigned int> > dof_indices(NDIM);

    // Integrate the tether force over the plate (in the reference
    // configuration, where the force per unit volume is defined).
    std::unique_ptr<FEBase> fe(FEBase::build(dim, dof_map.variable_type(0)));
    std::unique_ptr<QBase> qrule = QBase::build(QGAUSS, dim, FIFTH);
    fe->attach_quadrature_rule(qrule.get());
    const std::vector<double>& JxW = fe->get_JxW();
    const std::vector<libMesh::Point>& q_point = fe->get_xyz();
    const std::vector<std::vector<double> >& phi = fe->get_phi();
    boost::multi_array<double, 2> X_node;
    const TensorValue<double> FF_unused;
    const std::vector<const std::vector<double>*> var_data;
    const std::vector<const std::vector<VectorValue<double> >*> grad_var_data;
    VectorValue<double> F;
    libMesh::Point X;
    double F_integral[NDIM];
    for (unsigned int d = 0; d < NDIM; ++d) F_integral[d] = 0.0;
    const auto el_end = mesh.active_local_elements_end();
    for (auto el_it = mesh.active_local_elements_begin(); el_it != el_end; ++el_it)
    {
        Elem* const elem = *el_it;
        fe->reinit(elem);
        for (unsigned int d = 0; d < NDIM; ++d)
        {
            dof_map.dof_indices(elem, dof_indices[d], d);
        }
        get_values_for_interpolation(X_node, *X_ghost_vec, dof_indices);
        for (unsigned int qp = 0; qp < qrule->n_points(); ++qp)
        {
            interpolate(X, qp, X_node, phi);
            target_force_function(
                F, FF_unused, X, q_point[qp], elem, var_data, grad_var_data, loop_time, nullptr);
            for (unsigned int d = 0; d < NDIM; ++d) F_integral[d] += F(d) * JxW[qp];
        }
    }
    IBTK_MPI::sumReduction(F_integral, NDIM);

    // The range of J since the last call. (A process without any part of the
    // plate keeps the starting values, which the reductions ignore.)
    const double J_min = IBTK_MPI::minReduction(J_minimum);
    const double J_max = IBTK_MPI::maxReduction(J_maximum);
    J_minimum = std::numeric_limits<double>::max();
    J_maximum = -std::numeric_limits<double>::max();

    pout << "tether force =";
    for (unsigned int d = 0; d < NDIM; ++d) pout << " " << F_integral[d];
    pout << "   J from " << J_min << " to " << J_max << "\n";

    if (IBTK_MPI::getRank() == 0)
    {
        const string force_file_name = data_dump_dirname + "/tether_force.txt";
        const bool new_file = !std::ifstream(force_file_name).good();
        std::ofstream force_file(force_file_name, std::ios::app);
        if (new_file) force_file << "# time Fx Fy Fz (total tether force on the plate)\n";
        force_file.precision(10);
        force_file << loop_time;
        for (unsigned int d = 0; d < NDIM; ++d) force_file << " " << F_integral[d];
        force_file << "\n";
    }
    return;
} // output_data
