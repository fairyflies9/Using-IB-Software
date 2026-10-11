#!/bin/bash
#SBATCH --job-name=band-sweep
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --time=00:30:00
#SBATCH --array=1-3
#SBATCH --output=sweep-%A_%a.out

module load gnu13 openmpi5
source ~/autoibamr/configuration/enable.sh
cd "$SLURM_SUBMIT_DIR"

# Line i of params.txt holds the viscosity for array task i.
MU=$(sed -n "${SLURM_ARRAY_TASK_ID}p" params.txt)
RUN=run_${SLURM_ARRAY_TASK_ID}
mkdir -p "$RUN"
cp rubber_band_512.vertex rubber_band_512.spring "$RUN"/
# Copy input2d into the run folder, replacing the MU line by name.
awk -v mu="$MU" '/^MU[ \t]*=/ {print "MU = " mu; next} {print}' input2d > "$RUN"/input2d
cd "$RUN"
mpirun -np "$SLURM_NTASKS" ../build/main2d input2d
