import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
const OUT = process.argv[2];
const req = createRequire(path.join(process.argv[3], "package.json"));
const { chromium } = req("playwright");
const resp = fs.readFileSync(path.join(OUT, "fl_hw.json"), "utf8");
fs.mkdirSync(path.join(OUT, "shots"), { recursive: true });
const browser = await chromium.launch({ executablePath: process.env.CHROME });
const ctx = await browser.newContext({ viewport: { width: 1440, height: 810 }, deviceScaleFactor: 2 });
const page = await ctx.newPage();
const logs = [];
page.on("console", (m) => logs.push(m.type() + ": " + m.text().slice(0, 300)));
page.on("pageerror", (e) => logs.push("pageerror: " + e.message));
await page.route("http://localhost:8000/**", async (route) => {
  const r = route.request();
  const cors = { "access-control-allow-origin": "http://localhost:3010", "access-control-allow-credentials": "true", "access-control-allow-headers": "*", "access-control-allow-methods": "*" };
  if (r.method() === "OPTIONS") return route.fulfill({ status: 204, headers: cors });
  await new Promise((res) => setTimeout(res, 4000));
  return route.fulfill({ status: 200, headers: { ...cors, "content-type": "application/json" }, body: resp });
});
const shot = (n) => page.screenshot({ path: path.join(OUT, "shots", n + ".png") });
const dump = async (n) => {
  const html = await page.evaluate(() => document.documentElement.outerHTML);
  fs.writeFileSync(path.join(OUT, "dom_" + n + ".html"), html);
};
await page.goto("http://localhost:3010/", { waitUntil: "networkidle" });
await page.waitForSelector("canvas", { timeout: 60000 });
await page.waitForTimeout(2500);
const fontInfo = await page.evaluate(() => ({
  body: getComputedStyle(document.body).fontFamily,
  h1: getComputedStyle(document.querySelector("h1")).fontFamily,
  loaded: [...document.fonts].filter((f) => f.status === "loaded").map((f) => f.family + " " + f.weight + " " + f.style),
  check: document.fonts.check("16px 'Plus Jakarta Sans'"),
}));
fs.writeFileSync(path.join(OUT, "fonts.json"), JSON.stringify(fontInfo, null, 1));
await shot("s0_initial"); await dump("s0");
// css
const css = await page.evaluate(() => [...document.styleSheets].map((s) => { try { return [...s.cssRules].map((r) => r.cssText).join("\n"); } catch (e) { return "/* blocked " + s.href + " */"; } }).join("\n"));
fs.writeFileSync(path.join(OUT, "app.css"), css);
await page.hover("select[aria-label=Form]");
await page.waitForTimeout(300);
await shot("s0b_hover_select");
await page.selectOption("select[aria-label=Form]", "FL:FL__form_hw_POL987654321.pdf");
await page.waitForTimeout(3000);
await shot("s1_handwritten"); await dump("s1");
const geom1 = await page.evaluate(() => {
  const r = (el) => { const b = el.getBoundingClientRect(); return { x: b.x, y: b.y, w: b.width, h: b.height }; };
  const btns = [...document.querySelectorAll("button")].map((b) => ({ t: b.textContent.trim(), ...r(b) }));
  return { select: r(document.querySelector("select")), canvas: r(document.querySelector("canvas")), canvasPx: [document.querySelector("canvas").width, document.querySelector("canvas").height], btns };
});
fs.writeFileSync(path.join(OUT, "geom1.json"), JSON.stringify(geom1, null, 1));
await page.hover("text=Process Form");
await page.waitForTimeout(300);
await shot("s1b_hover_process");
await page.click("text=Process Form");
await page.waitForTimeout(800);
await shot("s2_processing"); await dump("s2");
await page.waitForSelector("text=Executive Summary", { timeout: 30000 });
await page.waitForTimeout(1500);
await shot("s3_results"); await dump("s3");
// hover policy number in key fields
const keyRows = page.locator("table").first().locator("tbody tr");
const n = await keyRows.count();
for (let i = 0; i < n; i++) {
  await keyRows.nth(i).hover();
  await page.waitForTimeout(250);
  await shot("s4_hover_key_" + i);
  if (i === 0) await dump("s4");
}
const polys = await page.evaluate(() => [...document.querySelectorAll("polygon")].map((p) => p.getAttribute("points")));
fs.writeFileSync(path.join(OUT, "polys_key0.json"), JSON.stringify(polys));
// open Low Confidence details
await page.mouse.move(5, 400);
await page.click("summary:has-text('Low Confidence Fields')");
await page.waitForTimeout(600);
await shot("s5_low_open"); await dump("s5");
const row = page.locator("tr:has-text('COMPANY NAME')").first();
await row.scrollIntoViewIfNeeded();
await row.hover();
await page.waitForTimeout(400);
await shot("s5b_company_hover"); await dump("s5b");
await row.locator("button[aria-label^='Edit']").click();
await page.waitForTimeout(300);
await shot("s6_edit");
const input = row.locator("input");
await input.fill("Pacific E-Commerce Logistics, Inc.");
await page.waitForTimeout(300);
await shot("s6b_typed"); await dump("s6b");
await row.locator("button[aria-label^='Approve']").click();
await page.waitForTimeout(500);
await shot("s7_approved"); await dump("s7");
// approve all remaining low-confidence rows (in the low-confidence table = 2nd table)
const lowTable = page.locator("table").nth(1);
const lowRows = lowTable.locator("tbody tr");
const ln = await lowRows.count();
for (let i = 0; i < ln; i++) {
  const b = lowRows.nth(i).locator("button[aria-label^='Approve']");
  const cls = await b.getAttribute("class");
  if (!cls.includes("border-emerald-200")) { await b.scrollIntoViewIfNeeded(); await b.click(); }
}
await page.waitForTimeout(500);
await page.evaluate(() => document.querySelector(".overflow-y-auto").scrollTo(0, 0));
await page.waitForTimeout(500);
await shot("s8_all_reviewed"); await dump("s8");
await page.hover("button:has-text('Export')");
await page.waitForTimeout(300);
await shot("s8b_export_hover");
await page.click("button:has-text('Export')");
await page.waitForTimeout(800);
await shot("s9_dialog"); await dump("s9");
fs.writeFileSync(path.join(OUT, "console.log"), logs.join("\n"));
await browser.close();
console.log("done", JSON.stringify(fontInfo));
