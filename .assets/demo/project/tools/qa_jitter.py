# Consecutive-frame stability over holds where nothing should move: mean |diff| and count of pixels changing > 12 levels.
import subprocess
import sys

import numpy as np

v = sys.argv[1]
W, H = 1920, 1080
for spec in sys.argv[2:]:
    name, start, end = spec.split(":")
    t0, t1 = float(start), float(end)
    n = int(round((t1 - t0) * 30)) + 1
    raw = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-ss",
            str(t0),
            "-i",
            v,
            "-frames:v",
            str(n),
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
        capture_output=True,
    ).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.int16)
    d = np.abs(np.diff(a, axis=0))
    means = d.reshape(d.shape[0], -1).mean(1)
    big = (d > 12).reshape(d.shape[0], -1).sum(1)
    print(
        f"{name:12s} frames={len(a)} mean|diff| max={means.max():.3f} changed-px max={big.max()} per-frame={list(big)}",
    )
