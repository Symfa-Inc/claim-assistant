(function () {
  "use strict";
  var D = window.__CA_DATA, G = D.geom;
  // Keep every transform 2D: force3D "auto" promotes the camera to a compositor layer that Chrome rasterizes
  // at 1x and stretches (soft zooms, text flipping between a crisp and a soft copy).
  gsap.config({ force3D: false });
  var tl = gsap.timeline({ paused: true });
  var APP0 = 6.9; // this scene's host data-start in index.html; every time below is a GLOBAL second
  var T = function (g) { return Math.max(0, +(g - APP0).toFixed(4)); };
  var FPS = 30;
  var $ = function (id) { return document.getElementById(id); };
  function fromTo(t, a, b, g) {
    b.immediateRender = false;
    tl.fromTo(t, a, b, T(g));
    if (b.filter === "blur(0px)") tl.set(t, { filter: "none" }, T(g + (b.duration || 0.5) + 0.001));
  }
  function to(t, v, g) { tl.to(t, v, T(g)); }
  function set(t, v, g) { tl.set(t, v, T(g)); }

  // ---------------- camera (app space 1440 x 810, frame 1920 x 1080) ----------------
  var CAM = "#ca-cam";
  var camNow = null;
  function camAt(cx, cy, s) {
    var hw = 960 / s, hh = 540 / s;
    cx = Math.min(Math.max(cx, hw), 1440 - hw);
    cy = Math.min(Math.max(cy, hh), 810 - hh);
    return { x: +(960 - cx * s).toFixed(3), y: +(540 - cy * s).toFixed(3), scale: s };
  }
  function camSet(g, f) { camNow = camAt(f[0], f[1], f[2]); set(CAM, camNow, g); }
  function cam(g, f, d) {
    var v = camAt(f[0], f[1], f[2]); camNow = v;
    to(CAM, { x: v.x, y: v.y, scale: v.scale, duration: d || 1.0, ease: "power2.inOut" }, g);
  }
  function scr(ax, ay) { return { x: ax * camNow.scale + camNow.x, y: ay * camNow.scale + camNow.y }; }

  // ---------------- right-panel scroll ----------------
  var RTOP = G["r-res"].y;
  var scrollNow = 0;
  function scrollSet(g, s) { scrollNow = s; set("#ca-rscroll", { y: -s }, g); }
  function scrollTo(g, s, d, ease) { scrollNow = s; to("#ca-rscroll", { y: -s, duration: d || 1.0, ease: ease || "power2.inOut" }, g); }
  function cy(el) { return el.y + el.h / 2 - scrollNow; } // app-space y of a right-panel element at the current scroll
  function cxm(el) { return el.x + el.w / 2; }

  // ---------------- cursor ----------------
  var CUR = "#ca-cursor", HX = 5.5, HY = 2.5;
  var cur = { x: 0, y: 0 };
  function curSet(g, x, y, op) { cur = { x: x, y: y }; set(CUR, { x: x - HX, y: y - HY, opacity: op == null ? 1 : op }, g); }
  function curMove(g, x, y, d, ease) {
    var from = cur; cur = { x: x, y: y };
    to(CUR, { x: x - HX, y: y - HY, duration: d || 0.7, ease: ease || "power3.inOut" }, g);
    return { from: from, to: cur, g: g, d: d || 0.7, ease: ease || "power3.inOut" };
  }
  function curShow(g) { fromTo(CUR, { opacity: 0 }, { opacity: 1, duration: 0.2, ease: "power1.out" }, g); }
  function curHide(g) { to(CUR, { opacity: 0, duration: 0.25, ease: "power1.in" }, g); }
  function click(g, fast) {
    to(CUR, { scale: 0.84, duration: fast ? 0.035 : 0.07, ease: "power2.out" }, g);
    to(CUR, { scale: 1, duration: fast ? 0.06 : 0.14, ease: "power2.out" }, g + (fast ? 0.04 : 0.09));
  }
  function press(sel, g, fast) {
    to(sel, { scale: 0.96, duration: fast ? 0.035 : 0.07, ease: "power2.out" }, g);
    to(sel, { scale: 1, duration: fast ? 0.07 : 0.16, ease: "power2.out" }, g + (fast ? 0.04 : 0.09));
  }

  // per-frame text sets (seek-safe counters)
  function countText(el, g, d, fn, ease) {
    var e = gsap.parseEase(ease || "power2.out");
    var n = Math.max(1, Math.round(d * FPS));
    var last = null;
    for (var f = 0; f <= n; f++) {
      var s = fn(e(f / n));
      if (s !== last) { set(el, { textContent: s }, g + f / FPS); last = s; }
    }
  }
  function swap(a, b, g, d) {
    d = d || 0.16;
    fromTo(a, { opacity: 1 }, { opacity: 0, duration: d * 0.8, ease: "power2.in" }, g);
    fromTo(b, { opacity: 0 }, { opacity: 1, duration: d, ease: "power2.out" }, g + d * 0.35);
  }

  // ---------------- callouts (screen space) ----------------
  // k: id letter; anchor in app space; dx/dy: where the leader line ends, in screen px; side "r" box right of
  // that point, "l" box left of it.
  function callout(k, g, hold, ax, ay, dx, dy, side, text) {
    var el = "#call-" + k, a = scr(ax, ay);
    var box = $("call-" + k + "-box"), line = $("call-" + k + "-line");
    $("call-" + k + "-t").textContent = text;
    var len = Math.sqrt(dx * dx + dy * dy), ang = Math.atan2(dy, dx) * 180 / Math.PI;
    line.style.width = len.toFixed(1) + "px";
    box.style.top = dy + "px";
    box.style.transform = "translateY(-50%)";
    if (side === "l") { box.style.left = "auto"; box.style.right = (-dx) + "px"; } else { box.style.left = dx + "px"; }
    set(el, { x: a.x, y: a.y }, g);
    set(el + "-line", { rotation: ang, scaleX: 0 }, g);
    set(el + " .ca-call-dot", { scale: 0 }, g);
    set(el + "-box", { opacity: 0, filter: "blur(6px)" }, g);
    set(el, { opacity: 1 }, g);
    fromTo(el + " .ca-call-dot", { scale: 0 }, { scale: 1, duration: 0.24, ease: "back.out(2)" }, g);
    fromTo(el + "-line", { scaleX: 0 }, { scaleX: 1, duration: 0.28, ease: "power3.out" }, g + 0.08);
    fromTo(el + "-box", { opacity: 0, filter: "blur(6px)" }, { opacity: 1, filter: "blur(0px)", duration: 0.22, ease: "power2.out" }, g + 0.2);
    to(el, { opacity: 0, duration: 0.2, ease: "power2.in" }, g + hold);
  }

  // ---------------- rows ----------------
  function rowOn(pfx, i, g) {
    to("#" + pfx + "-r" + i, { backgroundColor: "rgba(240,253,250,1)", boxShadow: "inset 5px 0 0 -3px rgba(13,148,136,1)", duration: 0.1, ease: "power1.out" }, g);
  }
  function rowOff(pfx, i, g) {
    to("#" + pfx + "-r" + i, { backgroundColor: "rgba(240,253,250,0)", boxShadow: "inset 0px 0 0 0px rgba(13,148,136,0)", duration: 0.14, ease: "power1.in" }, g);
  }
  function boxOn(id, g) { fromTo("#" + id, { opacity: 0 }, { opacity: 1, duration: 0.12, ease: "power1.out" }, g); }
  function boxOff(id, g) { to("#" + id, { opacity: 0, duration: 0.12, ease: "power1.in" }, g); }
  var reviewed = 0;
  function approve(i, g, fast) {
    var r = "#low-r" + i;
    to(r + "-ok", { borderColor: "#a7f3d0", backgroundColor: "#ecfdf5", color: "#059669", duration: fast ? 0.06 : 0.12, ease: "power1.out" }, g);
    fromTo(r + "-bar2", { scaleX: 0 }, { scaleX: 1, duration: fast ? 0.2 : 0.4, ease: "power2.out" }, g + 0.02);
    // out, then in: the two labels never sit on top of each other
    fromTo(r + "-c0", { opacity: 1 }, { opacity: 0, duration: fast ? 0.05 : 0.08, ease: "power1.in" }, g + 0.02);
    fromTo(r + "-c1", { opacity: 0 }, { opacity: 1, duration: fast ? 0.08 : 0.14, ease: "power2.out" }, g + (fast ? 0.07 : 0.1));
    reviewed += 1;
    set("#chip-rev-n", { textContent: String(reviewed) }, g + 0.02);
  }

  // =============== initial state ===============
  gsap.set(CUR, { x: 700, y: 400, opacity: 0, scale: 1, transformOrigin: "5.5px 2.5px" });
  gsap.set(".ca-bar2", { scaleX: 0, transformOrigin: "0% 50%" });
  gsap.set("#ca-rscroll", { y: 0 });
  gsap.set("#menu-form", { x: G["sel-form"].x, y: G["sel-form"].y + G["sel-form"].h + 4, opacity: 0 });
  set(CUR, { opacity: 0, scale: 1 }, APP0);
  set(".ca-bar2", { scaleX: 0 }, APP0);
  set("#low-details", { "--rot": "0deg" }, APP0);
  set("#low-body", { height: 0 }, APP0);
  set("#chip-rev-n", { textContent: "0" }, APP0);
  ["a", "b", "c", "d", "e", "f", "g"].forEach(function (k) { set("#call-" + k, { opacity: 0 }, APP0); });

  // camera presets [cx, cy, scale]
  var F_TOOL = [400, 225, 2.4];
  var F0 = [720, 405, 4 / 3];
  var SUM = G["card-sum"];
  var F_SUM = [SUM.x + SUM.w / 2, SUM.y + SUM.h / 2, Math.min(1920 / (SUM.w + 64), 1080 / (SUM.h + 36))];
  var F_TRACE = [780, 405, 1.5];
  camSet(APP0, F_TOOL);

  // =============== 1. pick the form, process it ===============
  var SEL = G["sel-form"], PR = G["btn-process"];
  curSet(7.5, 760, 360, 0); curShow(7.5);
  curMove(7.55, SEL.x + SEL.w * 0.42, SEL.y + SEL.h / 2 + 3, 0.8);
  to("#sel-form-a", { borderColor: "#cbd5e1", duration: 0.12 }, 8.33);
  click(8.6); to("#sel-form-a", { backgroundColor: "#f8fafc", duration: 0.06 }, 8.6); to("#sel-form-a", { backgroundColor: "#ffffff", duration: 0.18 }, 8.7);
  fromTo("#menu-form", { opacity: 0, scaleY: 0.96 }, { opacity: 1, scaleY: 1, duration: 0.2, ease: "power2.out" }, 8.66);
  var MTOP = SEL.y + SEL.h + 4 + 4; // first row top (menu y + padding)
  // the highlight follows the cursor tip across the rows
  (function (mv) {
    var e = gsap.parseEase(mv.ease), n = Math.round(mv.d * FPS), prev = -1;
    for (var f = 0; f <= n; f++) {
      var yy = mv.from.y + (mv.to.y - mv.from.y) * e(f / n);
      var idx = Math.floor((yy - MTOP) / 30);
      if (idx < 0 || idx > 6) idx = -1;
      if (idx !== prev) {
        var g = mv.g + f / FPS;
        if (prev >= 0) set("#menu-form-i" + prev, { color: "#475569" }, g);
        if (idx >= 0) { set("#menu-form-i" + idx, { color: "#0f766e" }, g); set("#menu-form-hl", { y: idx * 30, opacity: 1 }, g); }
        else set("#menu-form-hl", { opacity: 0 }, g);
        prev = idx;
      }
    }
  })(curMove(8.95, SEL.x + 70, MTOP + 30 + 16, 0.55, "power2.inOut"));
  click(9.75); to("#menu-form-hl", { backgroundColor: "#ccfbf1", duration: 0.06 }, 9.75);
  to("#menu-form", { opacity: 0, scaleY: 0.98, duration: 0.14, ease: "power2.in" }, 9.86);
  to("#sel-form-a", { borderColor: "#e2e8f0", duration: 0.2 }, 9.86);
  swap("#sel-form-a", "#sel-form-b", 9.9);
  // the PDF preview changes to the handwritten form
  fromTo("#pdf-a", { opacity: 1 }, { opacity: 0, duration: 0.4, ease: "power2.inOut" }, 10.0);
  fromTo("#pdf-b", { opacity: 0 }, { opacity: 1, duration: 0.5, ease: "power2.inOut" }, 10.05);
  swap("#zoom-a", "#zoom-b", 10.1);

  curMove(10.7, PR.x + PR.w * 0.55, PR.y + PR.h / 2 + 3, 0.65);
  to("#btn-process", { backgroundColor: "#0f766e", duration: 0.12 }, 11.33);
  click(11.62); press("#btn-process", 11.62);
  // processing: Process Form -> Processing..., Reset becomes the red cancel
  to("#btn-process", { backgroundColor: "#cbd5e1", boxShadow: "0 0 0 0 rgba(0,0,0,0)", duration: 0.15 }, 11.7);
  swap("#btn-process-a", "#btn-process-b", 11.7, 0.14);
  to("#btn-reset", { backgroundColor: "#ef4444", color: "#ffffff", duration: 0.15 }, 11.7);
  fromTo("#proc-spin", { rotation: 0 }, { rotation: 360 * 2.4, duration: 2.4, ease: "none" }, 11.7);
  swap("#r-empty", "#r-proc", 11.75, 0.22);
  fromTo("#r-proc-spin", { rotation: 0 }, { rotation: 360 * 3, duration: 2.4, ease: "none" }, 11.75);
  cam(11.95, F0, 1.0);
  curHide(12.3);
  // results arrive (the app's own fade-in: 0.4 s ease-out, 6 px rise, 60 ms stagger)
  to("#r-proc", { opacity: 0, duration: 0.15, ease: "power1.in" }, 14.1);
  swap("#btn-process-b", "#btn-process-a", 14.1, 0.14);
  to("#btn-process", { backgroundColor: "#0d9488", boxShadow: "0 1px 2px 0 rgba(0,0,0,0.05)", duration: 0.15 }, 14.1);
  to("#btn-reset", { backgroundColor: "#f1f5f9", color: "#94a3b8", duration: 0.15 }, 14.1);
  ["#card-sum", "#card-key", "#card-low", "#card-all"].forEach(function (c, i) {
    fromTo(c, { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, 14.15 + i * 0.06);
  });
  countText("#chip-all-n", 14.3, 1.0, function (p) { return String(Math.round(p * D.total)); });
  countText("#chip-low-n", 14.3, 1.0, function (p) { return String(Math.round(p * D.nLow)); });

  // =============== 2. the coverage call ===============
  cam(14.9, F_SUM, 1.0);
  var B = G["sum-badge"];
  callout("b", 15.95, 2.0, B.x + B.w, B.y + B.h / 2, 80, -6, "r", "Coverage call, with its reasons");
  var CR0 = G["chip-rev"];
  callout("c", 16.9, 2.2, CR0.x + CR0.w + 8, CR0.y + CR0.h / 2, 44, 0, "r", "54 fields read, 31 flagged");
  // (sheet "Values, traced back to the page" covers 19.8-21.8)

  // =============== 3. every value traced to the page ===============
  var KEY = G["card-key"];
  scrollSet(20.2, Math.round(KEY.y - RTOP - 12));
  camSet(20.2, F_TRACE);
  var KR = G.keyRows;
  curSet(22.5, 1240, 760, 0); curShow(22.5);
  curMove(22.55, 1060, cy(KR[0]) + 3, 0.7);
  rowOn("key", 0, 23.24); boxOn("box-key-0", 23.25);
  var BX0 = G.boxes["box-key-0"];
  cam(23.6, [410, BX0.y + BX0.h / 2 + 24, 3.0], 1.0); // right edge of the view stays in the gutter before the results panel
  callout("d", 24.75, 1.8, BX0.x + BX0.w / 2, BX0.y + BX0.h + 2, -60, 150, "l", "Policy Number, read from here");
  cam(26.6, F_TRACE, 0.75);
  curMove(26.65, 1060, cy(KR[6]) - 40, 0.55);
  rowOff("key", 0, 26.8); boxOff("box-key-0", 26.8);
  rowOn("key", 6, 27.2); boxOn("box-key-6", 27.21);
  var BX6 = G.boxes["box-key-6"];
  callout("e", 27.4, 1.8, BX6.x + BX6.w * 0.42, BX6.y - 2, 50, -118, "r", "Values link back to their source");
  // (sheet "Fix what the model doubts" covers 29.7-31.7)

  // =============== 4. fix what the model doubts ===============
  rowOff("key", 6, 29.95); boxOff("box-key-6", 29.95);
  curHide(29.95);
  var maxClosed = Math.round(G.scrollH - G.lowBodyH - 730);
  scrollSet(30.0, maxClosed);
  var LS = G["low-summary"];
  curSet(32.5, 1180, 470, 0); curShow(32.5);
  curMove(32.55, LS.x + 120, cy(LS) + 2, 0.65);
  click(33.45);
  to("#low-details", { "--rot": "90deg", duration: 0.2, ease: "power2.out" }, 33.47);
  to("#low-body", { height: G.lowBodyH, duration: 0.6, ease: "power2.inOut" }, 33.5);
  set("#low-body", { height: "auto" }, 34.15);
  for (var i = 0; i < 7; i++) fromTo("#low-r" + i, { opacity: 0 }, { opacity: 1, duration: 0.25, ease: "power1.out" }, 33.55 + i * 0.05);
  // scroll the company-name row to the middle of the view (cursor parked on the scrollbar side)
  curMove(33.85, 1428, 470, 0.4, "power2.inOut");
  var CI = D.companyIdx, LR = G.lowRows, CR = LR[CI];
  var scrollC = Math.round(CR.row.y + CR.row.h / 2 - 430);
  scrollTo(34.0, scrollC, 1.0);
  curMove(35.05, 1100, 430 + 3, 0.55);
  rowOn("low", CI, 35.58); boxOn("box-low-" + CI, 35.6);
  var BXC = G.boxes["box-low-" + CI];
  callout("f", 35.55, 2.55, BXC.x + BXC.w, BXC.y + BXC.h / 2, 60, 120, "r", "Company read from the D.B.A. line");
  var F_ROW = [CR.row.x + CR.row.w / 2, 430, 2.4];
  cam(38.2, F_ROW, 0.95);
  // edit
  var ED = CR.ed, OK = CR.ok, VS = G.vstates;
  curMove(39.15, ED.x + ED.w / 2 + 1, cy(ED) + 3, 0.5);
  to("#low-r" + CI + "-ed", { borderColor: "#cbd5e1", color: "#334155", duration: 0.12 }, 39.65);
  click(39.85); press("#low-r" + CI + "-ed", 39.85);
  to("#low-r" + CI + "-ed", { borderColor: "#e2e8f0", color: "#64748b", duration: 0.2 }, 40.1);
  to("#low-r" + CI + "-vwrap", { height: VS.inp, duration: 0.16, ease: "power2.out" }, 39.9);
  swap("#low-r" + CI + "-v0", "#low-r" + CI + "-inp", 39.9, 0.16);
  var VW = G.company.vwrap;
  curMove(40.1, VW.x + VW.w * 0.6, VW.y - scrollNow + VS.inp / 2 + 2, 0.4);
  click(40.55);
  to("#low-r" + CI + "-inp", { borderColor: "#14b8a6", boxShadow: "0 0 0 2px #ccfbf1", duration: 0.12 }, 40.58);
  set("#low-r" + CI + "-caret", { opacity: 1 }, 40.6);
  set("#low-r" + CI + "-txt", { backgroundColor: "#b3d4fc" }, 40.82);
  // type the right name, one key at a time
  var NEW = "Pacific E-Commerce Logistics, Inc.";
  var tk = 41.1;
  set("#low-r" + CI + "-txt", { backgroundColor: "rgba(0,0,0,0)", textContent: NEW.slice(0, 1) }, tk);
  for (var c = 2; c <= NEW.length; c++) {
    tk += (NEW[c - 1] === " " ? 0.06 : 0.04) + ((c * 7) % 5) * 0.004;
    set("#low-r" + CI + "-txt", { textContent: NEW.slice(0, c) }, tk);
  }
  var typedEnd = tk; // ~42.6
  set("#low-r" + CI + "-caret", { opacity: 0 }, typedEnd + 0.5);
  set("#low-r" + CI + "-caret", { opacity: 1 }, typedEnd + 0.75);
  // approve
  curMove(42.7, OK.x + OK.w / 2 + 1, cy(OK) + 3, 0.45);
  to("#low-r" + CI + "-ok", { borderColor: "#6ee7b7", backgroundColor: "#ecfdf5", color: "#059669", duration: 0.12 }, 43.15);
  click(43.35); press("#low-r" + CI + "-ok", 43.35);
  set("#low-r" + CI + "-caret", { opacity: 0 }, 43.4);
  swap("#low-r" + CI + "-inp", "#low-r" + CI + "-v1", 43.4, 0.18);
  to("#low-r" + CI + "-vwrap", { height: VS.v1, duration: 0.22, ease: "power2.out" }, 43.42);
  approve(CI, 43.4, false);
  callout("g", 43.65, 1.6, CR.c.x + CR.c.w / 2, cy(CR.c) - 10, 95, -212, "l", "Fixed, approved, now 100%");

  // =============== 5. clear the queue ===============
  var dH = VS.v1 - VS.v0; // the edited row grew by this much; rows below it moved down
  function okAbs(i) { return LR[i].ok.y + LR[i].ok.h / 2 + (i > CI ? dH : 0); }
  var maxOpen = Math.round(G.scrollH + dH - 730);
  cam(45.35, F_TRACE, 0.9);
  rowOff("low", CI, 45.4);
  var Y0 = 300;
  var s0 = Math.round(okAbs(0) - Y0);
  scrollTo(45.45, s0, 0.9);
  curMove(45.9, LR[0].ok.x + LR[0].ok.w / 2 + 1, Y0 + 3, 0.7);
  var OKX = LR[0].ok.x + LR[0].ok.w / 2 + 1;
  var order = [];
  for (var j = 0; j < LR.length; j++) if (j !== CI) order.push(j);
  var tclick = 46.7, clicks = [];
  order.forEach(function (ri, n) {
    var target, sc = scrollNow;
    if (n < 3) {
      target = okAbs(ri) - sc;
      if (n > 0) curMove(tclick - 0.3, OKX, target + 3, 0.26, "power2.inOut");
      click(tclick); approve(ri, tclick, false);
      clicks.push({ t: tclick, fast: false });
      tclick += 0.4;
    } else {
      // fast-forward: the list scrolls under the cursor, one approval every 0.1 s
      var want = okAbs(ri) - (Y0 + 3 * 49);
      var nsc = Math.min(Math.max(want, sc), maxOpen);
      if (nsc !== sc) { to("#ca-rscroll", { y: -nsc, duration: 0.1, ease: "none" }, tclick - 0.1); scrollNow = nsc; }
      target = okAbs(ri) - nsc;
      if (Math.abs(target - cur.y + 3) > 0.5) curMove(tclick - 0.1, OKX, target + 3, 0.1, "none");
      click(tclick, true); approve(ri, tclick, true);
      clicks.push({ t: tclick, fast: true });
      tclick += 0.1;
    }
  });
  var lastClick = tclick - 0.1; // ~50.3
  // the queue is reviewed: Export unlocks (btn-primary)
  to("#btn-export", { backgroundColor: "#0d9488", color: "#ffffff", boxShadow: "0 1px 2px 0 rgba(0,0,0,0.05)", duration: 0.2 }, lastClick + 0.05);
  window.__CA_CLICKS = clicks;

  // =============== 6. export ===============
  curMove(50.55, 1428, cur.y, 0.25, "power2.out");
  scrollTo(50.75, 0, 1.0);
  cam(50.85, F_SUM, 1.0);
  scrollNow = 0;
  var EX = G["btn-export"];
  callout("a", 52, 1.55, EX.x, EX.y + EX.h / 2, -60, 96, "l", "Export unlocks after review");
  curMove(53.05, EX.x + EX.w * 0.55, EX.y + EX.h / 2 + 3, 0.65);
  to("#btn-export", { backgroundColor: "#0f766e", duration: 0.12 }, 53.7);
  click(53.95); press("#btn-export", 53.95);
  set("#dlg-overlay", { backdropFilter: "blur(4px)", webkitBackdropFilter: "blur(4px)" }, 54.0);
  fromTo("#dlg-overlay", { opacity: 0 }, { opacity: 1, duration: 0.3, ease: "power1.out" }, 54.02);
  fromTo("#dlg", { opacity: 0, y: 6 }, { opacity: 1, y: 0, duration: 0.4, ease: "power2.out" }, 54.06);
  var DL = G["dlg"], CF = G["dlg-confirm"];
  cam(54.3, [DL.x + DL.w / 2, DL.y + DL.h / 2, 2.4], 0.95);
  curMove(55.8, CF.x + CF.w * 0.5, CF.y + CF.h / 2 + 3, 0.6);
  to("#dlg-confirm", { backgroundColor: "#0f766e", duration: 0.12 }, 56.4);
  click(56.65); press("#dlg-confirm", 56.65);
  to("#dlg", { opacity: 0, y: 4, duration: 0.2, ease: "power2.in" }, 56.75);
  to("#dlg-overlay", { opacity: 0, duration: 0.25, ease: "power1.in" }, 56.8);
  set("#dlg-overlay", { backdropFilter: "none", webkitBackdropFilter: "none" }, 57.1);
  to("#btn-export", { backgroundColor: "#0d9488", duration: 0.15 }, 56.8);
  curHide(57.1);
  cam(57.15, F0, 1.0);
  set("#ca-cam", { x: camNow.x }, 59.49); // hold

  window.__timelines = window.__timelines || {};
  window.__timelines["app"] = tl;
})();
