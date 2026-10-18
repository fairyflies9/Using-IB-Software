#!/bin/bash
# Puma (University of Arizona HPC): the frames of a movie of a finished IBAMR run, made on a compute node without a
# display (chapter 31), then encoded if ffmpeg is there. Submit from the run's folder (the one that holds viz_IB2d/):
#     sbatch visit_frames.slurm
# Not yet run on Puma: check `module avail visit` and `module avail ffmpeg` on a compute node first (chapter 31).
#SBATCH --job-name=visit-frames
#SBATCH --account=lauram9          # replace with your PI's group name
#SBATCH --partition=standard
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem-per-cpu=5gb          # a standard Puma core comes with 5 GB; more per core can mean a high-memory node
#SBATCH --time=01:00:00
#SBATCH --output=%x-%j.out

# Where the tutorial's scripts are (a clone of the repository), and what to draw.
S=$HOME/Using-IB-Software/examples/analysis
VIZ=viz_IB2d                       # a 2D run: visit_movie_frames.py draws 2D runs (3D pictures: visit_3d.py, chapter 27)
OUT=frames
ARGS="var=Omega lim=auto"          # visit_movie_frames.py keys: var=, lim=, meshes=, window=, size=, every=, ...

module load visit                  # Puma's VisIt module (visit/3.4.2 in 2026); or the full path of your own install
# module load ffmpeg               # if `module avail ffmpeg` lists one: then the movie is made below
cd "$SLURM_SUBMIT_DIR"
mkdir -p "$OUT"; touch "$OUT/.start"   # frames older than .start are from an earlier job
visit -nowin -cli -s "$S/visit_movie_frames.py" -- "$VIZ" "$OUT" $ARGS
n=$(find "$OUT" -maxdepth 1 -name "*.png" -newer "$OUT/.start" | wc -l)
echo "$n new frames in $OUT"       # count them: VisIt can say "completed" and write nothing (chapter 30)
[ "$n" -gt 0 ] || exit 1           # none written: the job ends FAILED in sacct, not COMPLETED

# Encoding: with an ffmpeg on the node (load its module above if `module avail ffmpeg` lists one, or a static build
# in ~/bin), make the MP4 here; otherwise copy the frames home (a few MB) and run make_movie.py there. Frames left in
# $OUT by an earlier job go into the movie too: give a new set of frames a new OUT.
if command -v ffmpeg > /dev/null 2>&1; then
    python3 "$S/make_movie.py" "$OUT" --fps 10 --out "$OUT/movie.mp4"
fi
