# Writes the sound-effect <audio> tags into index.html between the SFX markers.
# Clicks land 40 ms before the on-screen press (the file's attack peaks ~1 frame in); whooshes start with each wipe.
import pathlib
import re

root = pathlib.Path(__file__).resolve().parent.parent
idx = root / "index.html"
clicks = [8.6, 9.75, 11.62, 33.45, 39.85, 40.55, 43.35, 46.7, 47.1, 47.5, 53.95, 56.65]
fast = [round(47.9 + i * 0.1, 2) for i in range(27)]
wipes = [
    (4.45, "whoosh"),
    (6.95, "whoosh-b"),
    (19.3, "whoosh"),
    (21.8, "whoosh-b"),
    (29.2, "whoosh"),
    (31.7, "whoosh-b"),
    (58.89, "whoosh"),
]
dur = {"whoosh": 0.575, "whoosh-b": 0.75}
tags = []
for i, t in enumerate(clicks):
    tags.append(
        f'<audio id="sfx-click-{i + 1}" class="clip" src="assets/sfx/click-soft.mp3" data-start="{t - 0.04:.2f}" data-duration="0.36" data-track-index="11" data-volume="0.9"></audio>',
    )
for i, t in enumerate(fast):
    tags.append(
        f'<audio id="sfx-tick-{i + 1}" class="clip" src="assets/sfx/click-soft.mp3" data-start="{t - 0.04:.2f}" data-duration="0.36" data-track-index="{12 + i % 3}" data-volume="0.35"></audio>',
    )
tags.append(
    '<audio id="sfx-typing" class="clip" src="assets/sfx/typing.mp3" data-start="41.08" data-duration="1.5" data-track-index="15" data-volume="0.3"></audio>',
)
for i, (t, f) in enumerate(wipes):
    tags.append(
        f'<audio id="sfx-whoosh-{i + 1}" class="clip" src="assets/sfx/{f}.mp3" data-start="{t:.2f}" data-duration="{dur[f]}" data-track-index="16" data-volume="{0.16 if f == "whoosh" else 0.12}"></audio>',
    )
html = idx.read_text()
block = "<!-- SFX -->\n      " + "\n      ".join(tags) + "\n      <!-- /SFX -->"
if "<!-- SFX -->" in html:
    html = re.sub(r"<!-- SFX -->.*?<!-- /SFX -->", block, html, flags=re.S)
else:
    html = html.replace(
        'data-volume="1"></audio>\n',
        'data-volume="1"></audio>\n      ' + block + "\n",
        1,
    )
idx.write_text(html)
print(len(tags), "sfx tags")
