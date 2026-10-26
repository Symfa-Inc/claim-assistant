// Writes the three headline sheets (compositions/sheet-*.html). One transition for the whole film:
// a teal bar (the app header's accent bar) sweeps left to right and the #f8fafb sheet follows it in;
// on exit the bar sweeps again and the sheet is cut away behind it, revealing the app.
// Usage: node tools/build-sheets.mjs
import fs from "node:fs";
import path from "node:path";
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");

export const SHEETS = [
  { id: "sheet-1", words: ["Pick", "the", "claim", "form"], accent: 3, dur: 3.0 },
  { id: "sheet-2", words: ["Values,", "traced", "back", "to", "the", "page"], accent: 1, dur: 3.0 },
  { id: "sheet-3", words: ["Fix", "what", "the", "model", "doubts"], accent: 4, dur: 3.0 },
];

for (const s of SHEETS) {
  const p = s.id;
  const words = s.words.map((w, i) => `<span id="${p}-w${i}" class="${p}-w${i === s.accent ? " acc" : ""}">${w}</span>`).join(" ");
  const html = `<template>
<style>
@font-face { font-family: "Plus Jakarta Sans"; font-style: normal; font-weight: 200 800; src: url("assets/fonts/PlusJakartaSans-latin.woff2") format("woff2"); }
#root { position: absolute; inset: 0; overflow: hidden; }
#${p}-sheet { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; background: #f8fafb; }
#${p}-text { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; display: flex; align-items: center; justify-content: center;
  font-family: "Plus Jakarta Sans", sans-serif; font-weight: 700; font-size: 104px; line-height: 1; letter-spacing: -0.035em; color: #0f172a;
  -webkit-font-smoothing: antialiased; white-space: pre; }
#${p}-line { display: block; padding-left: 0.035em; }
#${p}-text .acc { color: #0d9488; }
#${p}-bar { position: absolute; left: 0; top: 0; width: 16px; height: 1080px; background: #0d9488; }
</style>
<div id="root" data-composition-id="${p}" data-width="1920" data-height="1080">
  <div id="${p}-sheet"><div id="${p}-text"><span id="${p}-line">${words}</span></div></div>
  <div id="${p}-bar"></div>
</div>
<script>
(function () {
  gsap.config({ force3D: false });
  var tl = gsap.timeline({ paused: true });
  var D = ${s.dur};
  var NI = { immediateRender: false };
  gsap.set("#${p}-sheet", { clipPath: "inset(0% 100% 0% 0%)" });
  gsap.set("#${p}-bar", { x: -16 });
  ${s.words.map((_, i) => `gsap.set("#${p}-w${i}", { opacity: 0 });`).join("\n  ")}
  // in: bar sweeps, sheet follows it (same duration and ease, so the edge stays on the bar)
  tl.fromTo("#${p}-bar", { x: -16 }, { x: 1920, duration: 0.5, ease: "power2.inOut", immediateRender: false }, 0);
  tl.fromTo("#${p}-sheet", { clipPath: "inset(0% 100% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 0%)", duration: 0.5, ease: "power2.inOut", immediateRender: false }, 0);
  // words: blur 8 -> 0 and opacity, 0.16 s each, 0.08 s apart, no translate; landed words do not move
  ${s.words.map((_, i) => `tl.fromTo("#${p}-w${i}", { opacity: 0, filter: "blur(8px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.16, ease: "power2.out", immediateRender: false }, ${(0.42 + i * 0.08).toFixed(2)});
  tl.set("#${p}-w${i}", { filter: "none" }, ${(0.42 + i * 0.08 + 0.17).toFixed(2)});`).join("\n  ")}
  // out: the bar sweeps again and the sheet is cut away behind it
  tl.fromTo("#${p}-bar", { x: -16 }, { x: 1920, duration: 0.5, ease: "power2.inOut", immediateRender: false }, D - 0.5);
  tl.fromTo("#${p}-sheet", { clipPath: "inset(0% 0% 0% 0%)" }, { clipPath: "inset(0% 0% 0% 100%)", duration: 0.5, ease: "power2.inOut", immediateRender: false }, D - 0.5);
  window.__timelines = window.__timelines || {};
  window.__timelines["${p}"] = tl;
})();
</script>
</template>
`;
  fs.writeFileSync(path.join(ROOT, "compositions", p + ".html"), html);
}
console.log("sheets written");
