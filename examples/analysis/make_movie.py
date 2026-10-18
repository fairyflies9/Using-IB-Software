"""make_movie.py: a folder of frames (PNG or JPEG) -> an MP4 (H.264) that plays everywhere, or a GIF (chapter 30).

    python make_movie.py <frames folder> [options]
options:
    --glob "f*.png"     which files, taken in sorted name order (gaps in the numbering do not matter)
    --fps 10            frames per second of the movie
    --crf 18            H.264 quality: 0 lossless ... 18 visually lossless ... 23 ffmpeg's default ... 51 worst
    --width 0           scale to this width (0: keep), the height follows
    --gif               write a GIF (its own 256-colour palette) instead of an MP4
    --out movie.mp4     the output file (default <frames folder>/movie.mp4 or movie.gif)
Needs ffmpeg on the PATH. The frames are first copied, in order, to a temporary folder as 00000.png, 00001.png, ...,
because ffmpeg's numbered-pattern input stops at the first missing number and its glob input does not exist in the
Windows builds. The size is padded to even numbers (H.264 with 4:2:0 colour refuses odd ones), and -pix_fmt yuv420p
is set (without it ffmpeg keeps full colour resolution from PNGs, High 4:4:4 Predictive, which QuickTime and most
players do not play). The ffmpeg command is printed.
"""
import argparse
import glob
import os
import shlex
import shutil
import subprocess
import sys
import tempfile

ap = argparse.ArgumentParser(description="frames -> MP4 or GIF with ffmpeg")
ap.add_argument("folder")
ap.add_argument("--glob", default="*.png")
ap.add_argument("--fps", type=float, default=10)
ap.add_argument("--crf", type=int, default=18)
ap.add_argument("--width", type=int, default=0)
ap.add_argument("--gif", action="store_true")
ap.add_argument("--out", default="")
a = ap.parse_args()

if shutil.which("ffmpeg") is None:
    sys.exit("ffmpeg is not on the PATH (Linux: apt install ffmpeg; Mac: brew install ffmpeg; Windows: a build "
             "from https://ffmpeg.org/download.html, its bin folder added to the PATH)")
files = sorted(glob.glob(os.path.join(a.folder, a.glob)))
if not files:
    sys.exit("no frames match %s" % os.path.join(a.folder, a.glob))
ext = os.path.splitext(files[0])[1].lower()
out = a.out or os.path.join(a.folder, "movie.gif" if a.gif else "movie.mp4")
tmp = tempfile.mkdtemp(prefix="frames_")
try:
    for i, f in enumerate(files):
        shutil.copyfile(f, os.path.join(tmp, "%05d%s" % (i, ext)))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "%g" % a.fps, "-i", os.path.join(tmp, "%05d" + ext)]
    scale = "scale=%d:-2:flags=lanczos," % a.width if a.width else ""
    if a.gif:
        cmd += ["-vf", scale + "split[a][b];[a]palettegen[p];[b][p]paletteuse"]
    else:
        cmd += ["-vf", scale + "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-crf", str(a.crf), "-movflags", "+faststart"]
    cmd.append(out)
    # the command as the shell would need it (the temporary folder of numbered copies is removed afterwards)
    print(subprocess.list2cmdline(cmd) if os.name == "nt" else shlex.join(cmd))
    r = subprocess.run(cmd)
    if r.returncode == 0:
        print("%d frames at %g fps = %.2f s -> %s (%.0f kB)" % (len(files), a.fps, len(files) / a.fps, out,
                                                               os.path.getsize(out) / 1000))
    sys.exit(r.returncode)
finally:
    shutil.rmtree(tmp, ignore_errors=True)
