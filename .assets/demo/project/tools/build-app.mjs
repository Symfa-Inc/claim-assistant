// Builds compositions/app.html: the Claim Assistant UI rebuilt as live DOM from the captured page.
// Inputs: assets/data/capture.json (the real /process response for the Florida handwritten form),
//         assets/data/app-tailwind.raw.css (the stylesheet captured from the running app),
//         src/app.style.css, src/app.timeline.js, assets/data/geom.json (measured by tools/measure.mjs).
// Usage: node tools/build-app.mjs
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), "..");
const rd = (p) => fs.readFileSync(path.join(ROOT, p), "utf8");
const D = JSON.parse(rd("assets/data/capture.json"));
const geomPath = path.join(ROOT, "assets/data/geom.json");
const GEOM = fs.existsSync(geomPath) ? JSON.parse(fs.readFileSync(geomPath, "utf8")) : null;

// ---------- the app's own CSS, made render-safe ----------
let css = rd("assets/data/app-tailwind.raw.css");
// keep only the latin Plus Jakarta Sans face, pointed at the project copy; drop the local() fallback face
css = css.replace(/@font-face\s*\{[^}]*\}/g, (m) => {
  if (/fba5a26ea33df6a3/.test(m)) return m.replace(/url\("[^"]+"\)/, 'url("assets/fonts/PlusJakartaSans-latin.woff2")');
  return "";
});
// transitions and CSS animations run on the browser clock: strip them, GSAP drives every state
css = css.replace(/\s*transition(-[a-z-]+)?\s*:[^;}]+;?/g, "");
css = css.replace(/\s*animation(-[a-z-]+)?\s*:[^;}]+;?/g, "");
css = css.replace(/scroll-behavior:\s*smooth;?/g, "").replace(/overflow-y:\s*scroll;?/g, "");
// pseudo-classes would react to the render's mouse: drop hover/focus variants
css = css.split("\n").filter((l) => !/:hover|:focus/.test(l)).join("\n");
// font stacks: the app renders Plus Jakarta Sans everywhere; Tailwind's preflight stacks name system fonts
css = css.replace(/font-family:\s*([^;}]+)/g, (m, v) => (v.trim() === '"Plus Jakarta Sans"' ? m : /monospace|SFMono|Menlo/i.test(v) ? "font-family: monospace" : /Plus Jakarta Sans|emoji|ui-sans-serif|system-ui/i.test(v) ? 'font-family: "Plus Jakarta Sans", sans-serif' : m));
fs.writeFileSync(path.join(ROOT, "assets/data/app-tailwind.css"), css);

// ---------- data ----------
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const aliasLabels = {
  policy_id: "Policy Number", first_name: "First Name", last_name: "Last Name", date_of_incident: "Incident Date",
  report_date: "Report Date", loss_type: "Type of Loss", loss_description: "Loss Description", loss_location: "Loss Location",
};
const keyOrder = Object.keys(aliasLabels);
const fields = D.form.map((f, i) => {
  const raw = f.answer?.value;
  const value = raw === null || raw === undefined ? "" : typeof raw === "string" ? raw : JSON.stringify(raw);
  const c = f.answer?.evidences?.[0]?.confidence;
  const ev = f.answer?.evidences?.[0]?.bounding_region || null;
  return {
    id: f.alias ?? `field_${i}`, alias: f.alias, label: f.text, keyLabel: f.alias ? aliasLabels[f.alias] ?? f.text : f.text,
    value, conf: typeof c === "number" ? `${Math.round(c * 100)}%` : "", region: ev,
  };
});
const keyFields = fields.filter((f) => f.alias).sort((a, b) => keyOrder.indexOf(a.alias) - keyOrder.indexOf(b.alias));
const pc = (s) => { const v = parseFloat(s); return Number.isNaN(v) ? 0 : v; };
const lowFields = fields.filter((f) => pc(f.conf) < 80);

// ---------- icons (paths from the app source) ----------
const ic = (d, cls = "h-3.5 w-3.5", sw = 2) =>
  `<svg class="${cls}" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="${sw}"><path stroke-linecap="round" stroke-linejoin="round" d="${d}"></path></svg>`;
const P = {
  minus: "M20 12H4", plus: "M12 4v16m8-8H4",
  fit: "M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5",
  doc: "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
  reset: "M4.5 12a7.5 7.5 0 0112.728-5.303l1.772 1.773M19.5 12a7.5 7.5 0 01-12.728 5.303L5 15.53M5 8.25V5.25h3",
  bulb: "M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z",
  upload: "M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12",
  edit: "M15.232 5.232l3.536 3.536M9 11l6.232-6.232a2.5 2.5 0 113.536 3.536L12.536 14.536a4 4 0 01-1.414.94L8 16l.524-3.122A4 4 0 019 11z",
  check: "M5 13l4 4L19 7",
  file: "M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z",
};
const spin = (id, cls = "h-3.5 w-3.5") =>
  `<svg id="${id}" class="${cls}" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>`;

// ---------- the claim table (ClaimTable component) ----------
function confParts(f) {
  const v = pc(f.conf);
  const hi = v >= 80, md = !hi && v >= 60;
  return { v, bar: hi ? "bg-emerald-400" : md ? "bg-amber-400" : "bg-rose-400", txt: hi ? "text-emerald-600" : md ? "text-amber-600" : "text-rose-500" };
}
function row(f, pfx, i, useKeyLabel) {
  const c = confParts(f);
  const rid = `${pfx}-r${i}`;
  const val = !f.value || f.value.toLowerCase() === "null" ? `<span class="text-slate-300">&mdash;</span>` : esc(f.value);
  const editable = pfx === "low" && f.label === "COMPANY NAME";
  const valCell = editable
    ? `<div id="${rid}-vwrap" class="ca-vwrap"><span id="${rid}-v0" class="ca-v0">${val}</span>` +
      `<div id="${rid}-inp" class="ca-input w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-[13px] text-slate-700"><span id="${rid}-sel" class="ca-sel"></span><span class="ca-itext"><span id="${rid}-txt">${val}</span><span id="${rid}-caret" class="ca-caret"></span></span><span class="ca-ispace"></span></div>` +
      `<span id="${rid}-v1" class="ca-v1">Pacific E-Commerce Logistics, Inc.</span></div>`
    : val;
  return `<tr id="${rid}" class="ca-tr">
<td class="py-2.5 pl-0.5 pr-4 font-medium text-slate-700 w-56">${esc(useKeyLabel ? f.keyLabel : f.label)}</td>
<td class="py-2.5 pr-4 text-slate-600">${valCell}</td>
<td class="py-2.5 pl-2 w-28"><div class="flex h-5 items-center gap-2"><div class="relative h-[3px] w-10 shrink-0 overflow-hidden rounded-full bg-slate-100"><div id="${rid}-bar" class="ca-bar h-full rounded-full ${c.bar}" style="width:${c.v}%"></div><div id="${rid}-bar2" class="ca-bar2 h-full rounded-full bg-emerald-400"></div></div>
<span class="ca-conf relative inline-flex h-5 w-12 shrink-0 items-center justify-end"><span id="${rid}-c0" class="ca-c0 inline-flex h-5 w-12 shrink-0 items-center justify-end gap-0.5 text-xs font-medium tabular-nums ${c.txt}">${esc(f.conf)}</span><span id="${rid}-c1" class="ca-c1 inline-flex h-5 w-12 shrink-0 items-center justify-end gap-0.5 text-xs font-medium tabular-nums text-emerald-600">${ic(P.check, "h-3 w-3 shrink-0", 2.5)}100%</span></span></div></td>
<td class="py-2.5 pl-3 text-right"><div class="inline-flex items-center gap-1"><button id="${rid}-ed" type="button" class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500">${ic(P.edit)}</button><button id="${rid}-ok" type="button" class="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500">${ic(P.check)}</button></div></td>
</tr>`;
}
function table(list, pfx, useKeyLabel) {
  return `<div class="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"><div class="mt-2 overflow-auto"><table id="${pfx}-table" class="w-full table-fixed text-left text-[13px] text-slate-600"><thead><tr class="border-b border-slate-100">
<th class="pb-2.5 pr-4 text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-[40%]">Field</th>
<th class="pb-2.5 pr-4 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Value</th>
<th class="pb-2.5 pl-2 text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-[12%]">Confidence</th>
<th class="pb-2.5 pl-3 text-right text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-[16%]">Actions</th>
</tr></thead><tbody class="divide-y divide-slate-100/80">${list.map((f, i) => row(f, pfx, i, useKeyLabel)).join("")}</tbody></table></div></div>`;
}

// ---------- highlight boxes on the PDF (same math as pdf-viewer.tsx: inches x 72 x zoom) ----------
const PAGE_W = 447.409, PAGE_H = 579, ZOOM = PAGE_H / 792;
function box(f, id) {
  const r = f.region; if (!r) return "";
  const xs = [], ys = [];
  for (let i = 0; i + 1 < r.polygon.length; i += 2) { xs.push(r.polygon[i]); ys.push(r.polygon[i + 1]); }
  const s = 72 * ZOOM;
  const x0 = Math.min(...xs) * s, x1 = Math.max(...xs) * s, y0 = Math.min(...ys) * s, y1 = Math.max(...ys) * s;
  return `<polygon id="${id}" class="ca-box fill-teal-200/25 stroke-teal-600" stroke-width="2" points="${x0.toFixed(2)},${y0.toFixed(2)} ${x1.toFixed(2)},${y0.toFixed(2)} ${x1.toFixed(2)},${y1.toFixed(2)} ${x0.toFixed(2)},${y1.toFixed(2)}"></polygon>`;
}
const boxes = [];
keyFields.forEach((f, i) => boxes.push(box(f, `box-key-${i}`)));
lowFields.forEach((f, i) => { if (f.label === "COMPANY NAME") boxes.push(box(f, `box-low-${i}`)); });

const summaryText = esc(D.executive_summary);
const conclusion = D.conclusion;
const total = fields.length, lowN = lowFields.length;
const companyIdx = lowFields.findIndex((f) => f.label === "COMPANY NAME");

const opts = ["Florida digital", "Florida handwritten", "New Hampshire digital", "New Hampshire handwritten", "Wisconsin digital", "Wisconsin handwritten", "Custom"];

const markup = `
<div id="ca-cam">
<div id="ca-app" class="antialiased">
<main class="flex flex-col bg-[#f8fafb]" style="min-height:810px">
  <header class="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-md"><div class="mx-auto flex items-center gap-3.5 px-6 py-2.5"><div class="h-8 w-1 rounded-full bg-accent"></div><div><h1 class="text-[17px] font-bold tracking-tight text-slate-900">Claim Assistant</h1><p class="text-[11px] leading-tight text-slate-400">Automate insurance claim intake with intelligent field extraction and mapping</p></div></div></header>
  <div class="mx-4 flex flex-1 flex-col items-start gap-5 py-2 lg:mx-6 lg:flex-row">
    <!-- left: PDF viewer -->
    <div class="flex w-full min-w-0 items-stretch lg:w-1/2 lg:shrink-0 lg:grow-0" style="height:738px">
      <div class="card flex w-full min-w-0 flex-1 flex-col overflow-hidden p-2.5">
        <div class="flex h-full min-h-0 w-full flex-1 flex-col gap-2">
          <div id="ca-toolbar" class="flex flex-row flex-wrap items-center gap-x-2.5 gap-y-2 rounded-xl border border-slate-200 bg-slate-50/60 px-3 py-2 w-full max-w-full min-w-0">
            <div class="flex items-center gap-1.5 shrink-0">
              <button type="button" class="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500">${ic(P.minus)}</button>
              <span class="ca-zoomwrap relative min-w-[44px] text-center text-[13px] font-medium tabular-nums text-slate-600"><span id="zoom-a" class="ca-zoom">69%</span><span id="zoom-b" class="ca-zoom ca-abs">73%</span></span>
              <button type="button" class="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500">${ic(P.plus)}</button>
              <button type="button" class="flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500">${ic(P.fit)}</button>
            </div>
            <div class="h-5 w-px bg-slate-200 shrink-0"></div>
            <label class="cursor-pointer inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-[13px] font-medium text-slate-600 shrink-0">${ic(P.doc)}Select</label>
            <div class="h-5 w-px bg-slate-200 shrink-0"></div>
            <div class="flex min-w-0 items-center gap-2"><span class="shrink-0 text-[13px] font-medium text-slate-500">Form</span>
              <div id="sel-form" class="ca-selwrap relative" style="width:160px">
                <select id="sel-form-a" class="ca-sel-el w-full min-w-0 max-w-[10rem] truncate rounded-md border border-slate-200 bg-white px-2.5 pr-8 py-1.5 text-[13px] text-slate-600"><option>Florida digital</option></select>
                <select id="sel-form-b" class="ca-sel-el ca-abs w-full min-w-0 max-w-[10rem] truncate rounded-md border border-slate-200 bg-white px-2.5 pr-8 py-1.5 text-[13px] text-slate-600"><option>Florida handwritten</option></select>
              </div>
            </div>
            <div class="flex-1 min-w-0"></div>
            <div class="flex items-center gap-2 shrink-0 ml-auto">
              <button id="btn-reset" type="button" class="relative inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3.5 py-1.5 text-[13px] font-medium bg-slate-100 text-slate-400">${ic(P.reset)}Reset</button>
              <button id="btn-process" type="button" class="relative inline-flex items-center gap-1.5 whitespace-nowrap rounded-lg px-3.5 py-1.5 text-[13px] font-medium text-white btn-primary shadow-sm"><span id="btn-process-a" class="inline-flex items-center gap-1.5">${ic(P.bulb)}Process Form</span><span id="btn-process-b" class="ca-abs ca-center inline-flex items-center gap-1.5">${spin("proc-spin", "h-3.5 w-3.5")}Processing...</span></button>
            </div>
          </div>
          <div id="ca-pdfarea" class="flex-1 min-h-0 overflow-hidden rounded-lg border border-slate-200 bg-white">
            <div class="flex min-h-full min-w-max flex-col items-center gap-2 text-[13px] text-slate-500">
              <div id="pdf-a" class="ca-pdf flex w-max flex-col items-center"><p class="text-xs text-slate-400">form_dg_POL123456789.pdf</p><div class="relative mx-auto" style="width:409.151px;height:579px"><img class="ca-page" src="assets/pdf/form-fl-digital.png" width="409" height="579" alt=""></div></div>
              <div id="pdf-b" class="ca-pdf ca-abs-top flex w-max flex-col items-center"><p class="text-xs text-slate-400">form_hw_POL987654321.pdf</p><div id="ca-page-hw" class="relative mx-auto" style="width:${PAGE_W}px;height:${PAGE_H}px"><img class="ca-page" src="assets/pdf/form-fl-handwritten.png" width="447" height="579" alt=""><svg class="pointer-events-none absolute inset-0 h-full w-full ca-boxes">${boxes.join("")}</svg></div></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <!-- right: results -->
    <div id="ca-right" class="relative flex w-full self-start flex-col lg:w-1/2 lg:shrink-0 lg:grow-0" style="height:730px">
      <!-- empty state (initial) -->
      <div id="r-empty" class="ca-rstate flex flex-1 flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-white p-8">
        <div class="flex flex-1 flex-col items-center justify-center gap-5">
          <div class="rounded-2xl bg-accent-subtle p-5">${ic(P.file, "h-10 w-10 text-accent", 1.5)}</div>
          <div class="text-center"><p class="text-sm font-medium text-slate-700">No form processed yet</p><p class="mt-1 text-[13px] text-slate-400">Choose a demo form or upload your own PDF, then click <span class="font-medium text-slate-600">"Process Form"</span>.</p></div>
        </div>
      </div>
      <!-- processing -->
      <div id="r-proc" class="ca-rstate card flex flex-1 flex-col items-center justify-center p-6">
        <div id="r-proc-spin" class="h-10 w-10 rounded-full border-[2.5px] border-slate-200 border-t-accent"></div>
        <span class="mt-4 text-[13px] text-slate-400">Analyzing document...</span>
      </div>
      <!-- results -->
      <div id="r-res" class="ca-rstate" style="height:730px;overflow:hidden">
        <div id="ca-rscroll" class="flex flex-col gap-4 pb-14">
          <div id="card-sum" class="card relative z-30 border-l-[3px] border-l-accent px-6 py-5">
            <details open=""><summary class="cursor-pointer select-none pl-5"><div class="ml-2 inline-flex w-[calc(100%-1.5rem)] items-center justify-between gap-3"><span class="text-[15px] font-semibold text-slate-800 inline-flex items-center gap-2">Executive Summary<span class="info-tip info-tip-down">i</span></span>
              <button id="btn-export" type="button" class="relative inline-flex items-center gap-1.5 rounded-lg px-3.5 py-1.5 text-[13px] font-medium bg-slate-100 text-slate-400">${ic(P.upload)}Export</button></div></summary>
              <div class="mt-4 pl-5">
                <div class="mb-3"><span id="sum-badge" class="inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium bg-amber-50 text-amber-700"><span class="h-1.5 w-1.5 rounded-full bg-amber-500"></span>${esc(conclusion)}</span></div>
                <p id="sum-text" class="text-[13px] leading-relaxed text-slate-600 text-justify">${summaryText}</p>
                <div id="sum-chips" class="mt-4 flex flex-wrap items-center gap-2 text-xs">
                  <span id="chip-all" class="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600">All:&nbsp;<span id="chip-all-n" class="ca-num">${total}</span></span>
                  <span id="chip-low" class="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-1 font-medium text-amber-700">Low confidence:&nbsp;<span id="chip-low-n" class="ca-num">${lowN}</span></span>
                  <span id="chip-rev" class="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700">Reviewed:&nbsp;<span id="chip-rev-n" class="ca-num">0</span></span>
                </div>
              </div>
            </details>
          </div>
          <div id="card-key" class="card relative z-20 px-6 py-5">
            <details open=""><summary class="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800"><span class="ml-2 inline-flex items-center gap-1.5">Key Fields<span class="info-tip info-tip-down">i</span><span class="inline-flex items-center rounded-full bg-accent-subtle px-2 py-0.5 text-xs font-medium text-accent">${keyFields.length}</span></span></summary>
              <div class="mt-4 pl-5">${table(keyFields, "key", true)}</div></details>
          </div>
          <div id="card-low" class="card relative z-10 px-6 py-5">
            <details id="low-details" class="ca-det" open=""><summary id="low-summary" class="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800"><span class="ml-2 inline-flex items-center gap-1.5">Low Confidence Fields<span class="info-tip info-tip-down">i</span><span class="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">${lowN}</span></span></summary>
              <div id="low-body" class="ca-lowbody"><div id="low-inner" class="mt-4 pl-5">${table(lowFields, "low", false)}</div></div></details>
          </div>
          <div id="card-all" class="card relative px-6 py-5">
            <details class="ca-det ca-closed"><summary class="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800"><span class="ml-2 inline-flex items-center gap-1.5">All Fields<span class="info-tip info-tip-down">i</span><span class="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">${total}</span></span></summary></details>
          </div>
        </div>
      </div>
    </div>
  </div>
</main>
<!-- export dialog -->
<div id="dlg-overlay" class="ca-overlay fixed-like inset-0 z-50 bg-black/20"></div>
<div id="dlg-wrap" class="ca-dlgwrap"><div id="dlg" class="card mx-4 w-full max-w-md p-6">
  <div class="flex items-start gap-3"><div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-subtle">${ic(P.check, "h-5 w-5 text-accent")}</div>
  <div><h2 class="text-[15px] font-semibold text-slate-800">Export Ready</h2><p class="mt-1 text-[13px] leading-relaxed text-slate-500">${lowN} of ${total} fields reviewed. The claim data will be exported to the ASC system for further processing.</p></div></div>
  <div class="mt-5 flex items-center justify-end gap-2"><button id="dlg-cancel" type="button" class="inline-flex items-center rounded-lg border border-slate-200 bg-white px-3.5 py-1.5 text-[13px] font-medium text-slate-600">Cancel</button><button id="dlg-confirm" type="button" class="btn-primary inline-flex items-center rounded-lg px-3.5 py-1.5 text-[13px] font-medium text-white shadow-sm">Confirm Export</button></div>
</div></div>
<!-- form menu (the native select popup, drawn in the app's popover style) -->
<div id="menu-form" class="ca-menu">
  <div id="menu-form-hl" class="ca-menu-hl"></div>
  ${opts.map((o, i) => `<div id="menu-form-i${i}" class="ca-menu-i">${esc(o)}${i === 0 ? `<span class="ca-menu-check">${ic(P.check, "h-3.5 w-3.5", 2.5)}</span>` : ""}</div>`).join("")}
</div>
<!-- cursor -->
<svg id="ca-cursor" width="24" height="24" viewBox="0 0 24 24"><path d="M5.5 2.5 L5.5 19.2 L9.6 15.4 L12.3 21.4 L15.1 20.2 L12.4 14.3 L18 14.3 Z" fill="#111827" stroke="#ffffff" stroke-width="1.5" stroke-linejoin="round"/></svg>
</div>
</div>
<!-- callouts live in screen space, above the camera -->
<div id="ca-callouts">
  ${["a", "b", "c", "d", "e", "f", "g"].map((k) => `<div id="call-${k}" class="ca-call"><div id="call-${k}-line" class="ca-call-line"></div><div class="ca-call-dot"></div><div id="call-${k}-box" class="ca-call-box"><span id="call-${k}-t"></span></div></div>`).join("\n  ")}
</div>
`;

const style = rd("src/app.style.css");
let timeline = rd("src/app.timeline.js");
const data = { geom: GEOM, nKey: keyFields.length, nLow: lowN, total, companyIdx, lowLabels: lowFields.map((f) => f.label), keyLabels: keyFields.map((f) => f.keyLabel) };
const html = `<template>
<style>
${css}
${style}
</style>
<div id="root" data-composition-id="app" data-width="1920" data-height="1080" data-layout-allow-overflow>
${markup}
</div>
<script>
window.__CA_DATA = ${JSON.stringify(data)};
${timeline}
</script>
</template>
`;
fs.writeFileSync(path.join(ROOT, "compositions/app.html"), html);
console.log("app.html", html.length, "bytes; key", keyFields.length, "low", lowN, "company idx", companyIdx, "geom", !!GEOM);
