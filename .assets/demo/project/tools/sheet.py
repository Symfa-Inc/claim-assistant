# usage: python3 sheet.py video out.png cols width t1 t2 ...
import io
import subprocess
import sys

from PIL import Image, ImageDraw

v, out, cols, w = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
ts = sys.argv[5:]
ims = []
for t in ts:
    png = subprocess.run(
        [
            "ffmpeg",
            "-loglevel",
            "error",
            "-ss",
            t,
            "-i",
            v,
            "-frames:v",
            "1",
            "-f",
            "image2pipe",
            "-vcodec",
            "png",
            "-",
        ],
        capture_output=True,
    ).stdout
    im = Image.open(io.BytesIO(png)).convert("RGB")
    im = im.resize((w, int(w * im.height / im.width)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, 70, 24), fill=(0, 0, 0))
    d.text((5, 5), t, fill=(255, 80, 80))
    ims.append(im)
h = ims[0].height
rows = (len(ims) + cols - 1) // cols
sh = Image.new("RGB", (cols * w, rows * h), (40, 40, 40))
for i, im in enumerate(ims):
    sh.paste(im, ((i % cols) * w, (i // cols) * h))
sh.save(out)
