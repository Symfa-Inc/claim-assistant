# Presence curve of elements that fade in: for each (name, t0, t1), decode frames t0..t1, region = pixels that differ
# between the first and the last frame; presence(f) = mean|f - first| / mean|last - first| inside that region.
import subprocess
import sys

import numpy as np

v = sys.argv[1]
W, H = 960, 540


def frames(t0, t1):
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
            "-vf",
            f"scale={W}:{H}",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "gray",
            "-",
        ],
        capture_output=True,
    ).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
    return a


checks = [x.split(":") for x in sys.argv[2:]]
for name, t0, t1 in checks:
    a = frames(float(t0), float(t1))
    first, last = a[0], a[-1]
    m = np.abs(last - first) > 25
    if m.sum() < 30:
        print(name, "no change")
        continue
    den = np.abs(last - first)[m].mean()
    pres = [float(np.abs(f - first)[m].mean() / den) for f in a]
    dips = [i for i in range(1, len(pres)) if pres[i] < pres[i - 1] - 0.05]
    print(
        f"{name:10s} px={int(m.sum()):6d} dips={dips} curve="
        + " ".join(f"{p:.2f}" for p in pres),
    )
