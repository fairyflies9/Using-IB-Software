#!/bin/bash
# Puma (University of Arizona HPC) job script for example IB/08.
# Submit from this folder with:  sbatch job.slurm
# The default run (END_TIME = 0.2) takes about 20 minutes on 4 cores. For the
# course's full run (END_TIME = 10, a million time steps, about 15 hours on 4
# cores) ask for more cores and time, for example --ntasks=16 and
# --time=24:00:00, and continue from the restart files if the job runs out of
# time (see README.md).
#SBATCH --job-name=ib08-glycocalyx-3d
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem-per-cpu=4gb
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out

# The same compiler and MPI modules that were used to build IBAMR.
module load gnu13 openmpi5
# Sets IBAMR_ROOT and the library paths. Change the path if IBAMR is
# installed somewhere else, for example in a shared group folder.
source ~/autoibamr/configuration/enable.sh

cd "$SLURM_SUBMIT_DIR"
mpirun -np "$SLURM_NTASKS" ./build/main3d input3d
