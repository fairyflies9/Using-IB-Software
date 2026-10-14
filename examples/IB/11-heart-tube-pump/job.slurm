#!/bin/bash
# Puma (University of Arizona HPC) job script for example IB/11.
# Submit from this folder with:  sbatch job.slurm
# To run another actuation mode, change the input file name on the last line
# (input2d.force-vp, input2d.force-peri, input2d.stiffness-peri, input2d.target-peri).
#SBATCH --job-name=ib11-heart-tube-pump
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --mem-per-cpu=4gb
#SBATCH --time=02:00:00
#SBATCH --output=%x-%j.out

# The same compiler and MPI modules that were used to build IBAMR.
module load gnu13 openmpi5
# Sets IBAMR_ROOT and the library paths. Change the path if IBAMR is
# installed somewhere else, for example in a shared group folder.
source ~/autoibamr/configuration/enable.sh

cd "$SLURM_SUBMIT_DIR"
mpirun -np "$SLURM_NTASKS" ./build/main2d input2d
