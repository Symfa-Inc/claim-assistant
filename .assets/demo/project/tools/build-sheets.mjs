// Writes the three headline sheets (compositions/sheet-*.html). One transition for the whole film, the
// house sheet whip: the full-frame #f8fafb sheet slides in from the right (x 2050 -> 0, 0.45 s power3.inOut,
// 10 px blur that clears 0.25-0.45 s) and leaves to the left at clip end - 0.45 s. A 16 px teal bar (the app
// header's accent bar) rides the sheet's leading edge on the way in and its trailing edge on the way out.
// Usage: node tools/build-sheets.mjs
import fs from "node:fs";
import path from "node:path";
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

// dx/dy: measured per-card corrections (px) that put the glyph ink box (cap top to baseline) at the frame
// centre (959.5, 539.5); see REVIEW.md "House style alignment".
export const SHEETS = [
  { id: "sheet-1", words: ["Pick", "the", "claim", "form"], accent: 3, dx: -3, dy: -2 },
  { id: "sheet-2", words: ["Values,", "traced", "back", "to", "the", "page"], accent: 1, dx: -0.5, dy: -2.5 },
  { id: "sheet-3", words: ["Fix", "what", "the", "model", "doubts"], accent: 4, dx: -3.5, dy: -2 },
];
const DUR = 2.4; // house clip length
const OUT = DUR - 0.45; // exit starts at clip end - 0.45 s (1.95 s)

for (const s of SHEETS) {
  const p = s.id;
  const words = s.words.map((w, i) => `<span id="${p}-w${i}" class="${p}-w${i === s.accent ? " acc" : ""}">${w}</span>`).join(" ");
  const html = `<template>
<style>
@font-face { font-family: "Plus Jakarta Sans"; font-style: normal; font-weight: 200 800; src: url("assets/fonts/PlusJakartaSans-latin.woff2") format("woff2"); }
#root { position: absolute; inset: 0; overflow: hidden; }
#${p}-sheet { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; background: #f8fafb; }
#${p}-text { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; display: flex; align-items: center; justify-content: center;
  font-family: "Plus Jakarta Sans", sans-serif; font-weight: 700; font-size: 104px; line-height: 1; letter-spacing: -0.035em; word-spacing: 0.11em; color: #0f172a;
  -webkit-font-smoothing: antialiased; white-space: nowrap; }
#${p}-line { display: block; transform: translate(${s.dx}px, ${s.dy}px); }
#${p}-text .acc { color: #0d9488; }
.${p}-bar { position: absolute; top: 0; width: 16px; height: 1080px; background: #0d9488; }
#${p}-bar-l { left: -16px; }
#${p}-bar-r { left: 1920px; }
</style>
<div id="root" data-composition-id="${p}" data-width="1920" data-height="1080">
  <div id="${p}-sheet" data-layout-allow-overflow><div id="${p}-text"><span id="${p}-line">${words}</span></div><div id="${p}-bar-l" class="${p}-bar"></div><div id="${p}-bar-r" class="${p}-bar"></div></div>
</div>
<script>
(function () {
  gsap.config({ force3D: false });
  var tl = gsap.timeline({ paused: true });
  // start states from frame 0: the sheet off-screen right and blurred, every word hidden
  gsap.set("#${p}-sheet", { x: 2050, filter: "blur(10px)" });
  ${s.words.map((_, i) => `gsap.set("#${p}-w${i}", { opacity: 0, filter: "blur(8px)" });`).join("\n  ")}
  // in: the whip, blur clears over its last 0.2 s
  tl.fromTo("#${p}-sheet", { x: 2050 }, { x: 0, duration: 0.45, ease: "power3.inOut", immediateRender: false }, 0);
  tl.fromTo("#${p}-sheet", { filter: "blur(10px)" }, { filter: "blur(0px)", duration: 0.2, ease: "power2.out", immediateRender: false }, 0.25);
  tl.set("#${p}-sheet", { filter: "none" }, 0.46);
  // words: blur 8 -> 0 and opacity, 0.16 s each, 0.08 s apart from +0.40 s, no translate; landed words do not move
  ${s.words.map((_, i) => `tl.fromTo("#${p}-w${i}", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power2.out", immediateRender: false }, ${(0.4 + i * 0.08).toFixed(2)});
  tl.set("#${p}-w${i}", { filter: "none" }, ${(0.4 + i * 0.08 + 0.17).toFixed(2)});`).join("\n  ")}
  // out: the whip continues to the left, blurring as it goes
  tl.fromTo("#${p}-sheet", { x: 0 }, { x: -2050, duration: 0.45, ease: "power3.inOut", immediateRender: false }, ${OUT.toFixed(2)});
  tl.fromTo("#${p}-sheet", { filter: "blur(0px)" }, { filter: "blur(10px)", duration: 0.22, ease: "power2.in", immediateRender: false }, ${OUT.toFixed(2)});
  window.__timelines = window.__timelines || {};
  window.__timelines["${p}"] = tl;
})();
</script>
</template>
`;
  fs.writeFileSync(path.join(ROOT, "compositions", p + ".html"), html);
}
console.log("sheets written");
