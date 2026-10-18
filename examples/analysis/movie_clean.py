"""movie_clean.py: remove the thin coloured lines of the AMR patch boundaries from frames already rendered (chapter 30).

usage: python movie_clean.py <frames folder> [<glob, default f*.png>] [<K, default 1>]
    -> writes <frames folder>/clean/<same names>
The lines come from the Subset plot of 'levels' that VisIt adds by itself when it opens a SAMRAI database (dumps.visit).
The fix is to delete that plot before rendering (DeleteAllPlots() right after OpenDatabase in a script; chapters 26
and 30); this script is a repair for frames made before.
A line pixel is one whose colour is a saturated primary or secondary (red, green, blue, cyan, magenta, yellow) and that
does not survive an opening by a (2K+1) x (2K+1) square (so it is at most 2K pixels thick); it is replaced by the mean
of the non-line pixels in its (2K+3) x (2K+3) neighbourhood (5 x 5 for K = 1). Green-dominant pixels are always
replaced (the 'difference' colour table has no green). Saturated blobs of the field thicker than 2K pixels keep their
interiors, but thin saturated features of the field are changed too: on IB/11 frames made without the Subset plot
(1200 x 800, limits +-103 1/s) it still changed 691-1490 pixels per frame, in the saturated layers along the tube's
walls. The Subset plot's legend is not removed.
"""
import glob
import os
import sys

import numpy as np
from PIL import Image


def shift_min(m, k):
    out = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            out &= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def shift_max(m, k):
    out = m.copy()
    for dy in range(-k, k + 1):
        for dx in range(-k, k + 1):
            out |= np.roll(np.roll(m, dy, 0), dx, 1)
    return out


def clean(src, dst):
    im = np.asarray(Image.open(src).convert("RGB")).astype(np.float32)
    r, g, b = im[..., 0], im[..., 1], im[..., 2]
    # a saturated primary, allowing for the anti-aliased blend of a thin line with the white background
    sat = ((r >= 170) & (r - np.maximum(g, b) >= 80)) | ((g >= 150) & (g - np.maximum(r, b) >= 60)) | ((b >= 170) & (b - np.maximum(r, g) >= 80))
    # the SAMRAI reader colours deeper levels cyan, magenta and yellow (saturated secondaries); thin ones only
    sat |= ((g >= 150) & (b >= 150) & (np.minimum(g, b) - r >= 80)) | ((r >= 170) & (b >= 170) & (np.minimum(r, b) - g >= 80)) | ((r >= 170) & (g >= 150) & (np.minimum(r, g) - b >= 80))
    thin = sat & ~shift_max(shift_min(sat, K), K)
    # green never occurs in the vorticity colour table, so every green-dominant pixel is a boundary line
    thin |= (g >= 150) & (g - np.maximum(r, b) >= 60)
    ok = thin
    if thin.any():
        keep = (~thin).astype(np.float32)
        acc = np.zeros_like(im); cnt = np.zeros(im.shape[:2], np.float32)
        R = K + 1                                     # reaches past the middle of a line 2K pixels thick
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                acc += np.roll(np.roll(im * keep[..., None], dy, 0), dx, 1)
                cnt += np.roll(np.roll(keep, dy, 0), dx, 1)
        ok = thin & (cnt > 0)
        im[ok] = acc[ok] / cnt[ok][:, None]
    Image.fromarray(im.clip(0, 255).astype(np.uint8)).save(dst)
    return int(ok.sum())                              # the pixels actually replaced


if len(sys.argv) < 2:
    sys.exit(__doc__)
folder = sys.argv[1]
K = int(sys.argv[3]) if len(sys.argv) > 3 else 1   # lines up to 2K pixels thick are removed
out = os.path.join(folder, "clean"); os.makedirs(out, exist_ok=True)
files = sorted(glob.glob(os.path.join(folder, sys.argv[2] if len(sys.argv) > 2 else "f*.png")))
n = sum(clean(f, os.path.join(out, os.path.basename(f))) for f in files)
print(folder, len(files), "frames, line pixels replaced:", n)
