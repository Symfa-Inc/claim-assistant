# Re-cuts the music bed's ending for the house end card (B2.11): fade-out from end card +3.9 s for 2.9 s,
# then digital silence to the end of the film.
# The v2 bed had its fade baked in from 62.5 s. This script replaces the tail from SPLICE onward with the
# same bars two bars earlier (the bed repeats bar to bar; lag found by cross-correlation near 2 bars), joined
# with a 50 ms equal-power crossfade, then applies a linear fade FADE_START..FADE_END and zeros after it.
# Usage: python3 tools/recut-bed.py <in.wav> <out.wav>   (run once on the v2 bed from commit 893d7be)
import sys
import wave

import numpy as np

SR = 48000
SPLICE = 62.3  # before the old baked fade starts (62.5 s)
FADE_START, FADE_END, TOTAL = (
    62.8,
    65.7,
    66.4,
)  # end card at 58.9 s: +3.9 s, +6.8 s, film end
BAR = 4 * 0.6175  # ~97.2 BPM, measured


def main(src: str, dst: str) -> None:
    with wave.open(src) as w:
        a = (
            np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16)
            .reshape(-1, 2)
            .astype(np.float64)
        )
    mono = a.mean(1)
    ref = mono[int(59.8 * SR) : int(62.3 * SR)]
    best = (-2.0, 0)
    for lag in range(int((2 * BAR - 0.03) * SR), int((2 * BAR + 0.03) * SR), 4):
        seg = mono[int(59.8 * SR) - lag : int(62.3 * SR) - lag]
        c = float(np.dot(ref, seg) / (np.linalg.norm(ref) * np.linalg.norm(seg) + 1e-9))
        if c > best[0]:
            best = (c, lag)
    corr, lag = best
    n = int(TOTAL * SR)
    out = np.zeros((n, 2))
    s = int(SPLICE * SR)
    out[:s] = a[:s]
    tail = a[s - lag : n - lag]
    out[s : s + len(tail)] = tail
    xf = int(0.05 * SR)
    t = np.linspace(0, np.pi / 2, xf)[:, None]
    out[s : s + xf] = a[s : s + xf] * np.cos(t) + a[s - lag : s - lag + xf] * np.sin(t)
    tt = np.arange(n) / SR
    g = np.clip((FADE_END - tt) / (FADE_END - FADE_START), 0, 1)
    out *= g[:, None]
    out = np.clip(np.round(out), -32768, 32767).astype(np.int16)
    with wave.open(dst, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(out.tobytes())
    print(
        f"lag {lag / SR:.4f} s (corr {corr:.3f}); wrote {n / SR:.2f} s, fade {FADE_START}-{FADE_END} s",
    )


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
