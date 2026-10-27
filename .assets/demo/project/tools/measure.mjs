// Measures the rebuilt app DOM (compositions/app.html, scripts stripped) so camera framings and cursor
// targets come from the recreation itself. Also writes comparison PNGs of the rebuild at 1440 x 810
// (scratch/compare/*.png) to hold against the live captures.
// Usage: CHROME=<chrome binary> node tools/measure.mjs <dir containing node_modules/playwright>
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const req = createRequire(path.join(process.argv[2], "package.json"));
const { chromium } = req("playwright");
const html = fs.readFileSync(path.join(ROOT, "compositions/app.html"), "utf8");
const inner = html.replace(/^<template>/, "").replace(/<\/template>\s*$/, "").replace(/<script>[\s\S]*<\/script>/, "");
const base = "file://" + ROOT + "/";
const browser = await chromium.launch({ executablePath: process.env.CHROME });
const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
const tmp = path.join(ROOT, "..", "scratch", "measure-page.html");
fs.writeFileSync(tmp, `<!doctype html><html><head><meta charset="utf-8"><base href="${base}"></head><body style="margin:0">${inner}</body></html>`);
await page.goto("file://" + tmp);
await page.evaluate(() => document.fonts.ready);
await page.waitForTimeout(400);
// results state, low-confidence body open
await page.addStyleTag({ content: "#r-empty{opacity:0!important}#card-sum,#card-key,#card-low,#card-all{opacity:1!important}#low-body{height:auto!important}" });
await page.waitForTimeout(100);
const geom = await page.evaluate(() => {
  const r = (el) => { if (typeof el === "string") el = document.getElementById(el); const b = el.getBoundingClientRect(); return { x: +b.x.toFixed(1), y: +b.y.toFixed(1), w: +b.width.toFixed(1), h: +b.height.toFixed(1) }; };
  const ids = ["chip-low", "chip-all", "ca-toolbar", "sel-form", "btn-process", "btn-reset", "ca-page-hw", "ca-right", "r-res", "r-proc", "r-empty", "ca-rscroll",
    "card-sum", "sum-badge", "sum-text", "sum-chips", "chip-all", "chip-low", "chip-rev", "btn-export", "card-key", "card-low", "low-summary",
    "low-inner", "card-all", "dlg", "dlg-confirm", "dlg-cancel"];
  const g = {};
  ids.forEach((id) => { g[id] = r(id); });
  g.keyRows = [...document.querySelectorAll("#key-table tbody tr")].map((tr) => r(tr));
  g.lowRows = [...document.querySelectorAll("#low-table tbody tr")].map((tr) => ({ row: r(tr), ok: r(tr.querySelector("[id$='-ok']")), ed: r(tr.querySelector("[id$='-ed']")), c: r(tr.querySelector(".ca-conf")) }));
  g.boxes = {};
  document.querySelectorAll(".ca-box").forEach((p) => { g.boxes[p.id] = r(p); });
  const inp = document.querySelector(".ca-input");
  if (inp) { const tr = inp.closest("tr"); g.company = { row: r(tr), vwrap: r(inp.parentElement), td: r(inp.closest("td")) }; }
  g.lowBodyH = document.getElementById("low-inner").getBoundingClientRect().height;
  g.scrollH = document.getElementById("ca-rscroll").getBoundingClientRect().height;
  // menu anchor = the select
  return g;
});
// heights of the edited value in each state
const vstates = await page.evaluate(() => {
  const w = document.querySelector(".ca-vwrap"); if (!w) return null;
  const h = (el) => el.getBoundingClientRect().height;
  const v0 = w.querySelector(".ca-v0"), v1 = w.querySelector(".ca-v1"), inp = w.querySelector(".ca-input");
  [v0, v1, inp].forEach((e) => (e.style.position = "static"));
  const out = { v0: h(v0), v1: h(v1), inp: h(inp) };
  [v0, v1, inp].forEach((e) => (e.style.position = ""));
  return out;
});
geom.vstates = vstates;
fs.writeFileSync(path.join(ROOT, "assets/data/geom.json"), JSON.stringify(geom, null, 1));
console.log(JSON.stringify({ company: geom.company, vstates, lowBodyH: geom.lowBodyH, scrollH: geom.scrollH, sum: geom["card-sum"], key: geom["card-key"], low: geom["card-low"] }));

// comparison shots at 1440 x 810, device scale 2 (matches the live captures)
const cmp = path.join(ROOT, "..", "scratch", "compare");
fs.mkdirSync(cmp, { recursive: true });
const p2 = await browser.newPage({ viewport: { width: 1440, height: 810 }, deviceScaleFactor: 2 });
await p2.goto("file://" + tmp);
await p2.evaluate(() => document.fonts.ready);
await p2.waitForTimeout(400);
await p2.addStyleTag({ content: "#ca-callouts{display:none!important}" });
await p2.screenshot({ path: path.join(cmp, "rebuild_s0.png") });
await p2.addStyleTag({ content: "#pdf-a{opacity:0!important}#pdf-b{opacity:1!important}#zoom-a{opacity:0!important}#zoom-b{opacity:1!important}#sel-form-a{opacity:0!important}#sel-form-b{opacity:1!important}" });
await p2.screenshot({ path: path.join(cmp, "rebuild_s1.png") });
await p2.addStyleTag({ content: "#r-empty{opacity:0!important}#card-sum,#card-key,#card-low,#card-all{opacity:1!important}" });
await p2.screenshot({ path: path.join(cmp, "rebuild_s3.png") });
await browser.close();
