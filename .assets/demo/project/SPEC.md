# SPEC: Claim Assistant product demo

GOAL:    a claims adjuster finishes the film knowing Claim Assistant reads a filled claim form, gives a coverage
         call with its reasons, shows where every value was read on the page, and makes them review the doubtful
         fields before the claim is exported.
OUTPUT:  HyperFrames, 1920 x 1080, 30 fps, H.264 yuv420p + AAC 48 kHz.
TIME:    66.4 s x 30 = 1992 frames. Music bed ~97 BPM (Lyria RealTime, generated), 1 beat = 0.62 s (18.6 frames),
         trimmed so a beat falls on 0.0 s. Sheet whips are timed so the sheet fully covers on a beat
         (4.95, 19.80, 29.70 s downbeats; the end card at 59.35 s, one frame before the 59.39 s beat).
LOOK:    the product's own system, nothing invented.
         ground #f8fafb (app main bg); cards #ffffff, 1 px #e2e8f0, 14 px radius (the app's .card);
         ink #0f172a / #334155, secondary #64748b; ONE accent #0d9488 (app --accent): the PDF evidence
         boxes, one word per headline, the callout rule and dot, the sheet's wipe bar, the URL on the end card.
         Brand mark (blue shield, .assets/logo.png) appears twice only: hook poster and end card.
         One family: Plus Jakarta Sans (the app's next/font, the captured latin woff2).
         Headlines 700 104 px (80 px cap-to-baseline ink), tracking -0.035em, word-spacing 0.11em, ink box centred
         on both axes within 2 px. Hook poster per the house layout: lockup at (160, 120), headline 104 px at cap
         top 298, hero column ink right edge at 1760.
         Callouts 600 30 px on white, 1 px #e2e8f0 border, 14 px radius, 4 px teal rule on the left edge,
         shadow 0 14 36 rgba(15,23,42,.14), a 2 px teal leader line to a 16 px teal dot with a 4 px white ring.
         The UI is the real app rebuilt as DOM from the captured page: Tailwind CSS captured from the running
         app (port 3010), the real /process response for the Florida handwritten form (backend on 8010),
         the PDF pages rendered at 216 dpi, at 1440 x 810 CSS px framed by a camera between 1.333x and 2.6x.
OBJECTS: cursor = black arrow with a 1.5 px white edge, 24 px in app space (32-62 px on screen).
         Form menu = the native select popup drawn in the app's popover style: white card, 10 px radius,
         30 px rows, hovered row #f0fdfa with #0f766e text, teal check on the current value.
         Evidence box = the app's own SVG polygon (fill teal-200/25, stroke teal-600, 2 px), same inches x 72 x
         zoom math as pdf-viewer.tsx.
MOTION:  camera moves power2.inOut 0.9-1.0 s, one at a time, never while a callout is up.
         cursor travel power3.inOut 0.4-0.8 s; press = cursor scale 0.86 + control scale 0.96 for ~4 frames.
         menu open 0.2 s power2.out (opacity, scaleY 0.96 -> 1); close 0.14 s power2.in.
         results arrive with the app's own fade-in (0.4 s ease-out, 6 px rise, 60 ms stagger).
         counts tick per frame (power2.out, integers); typing one key per 40-60 ms.
         sheet (house whip): the #f8fafb sheet slides in from the right, x 2050 -> 0 in 0.45 s power3.inOut,
         10 px blur clearing 0.25-0.45 s; it leaves to the left from clip end - 0.45 s with a 10 px blur.
         A 16 px teal bar rides its leading edge in and its trailing edge out. Clip 2.4 s.
         This is the only transition between chapters; inside chapters the camera does the work.
         headline words: blur 8 -> 0 px + opacity, 0.16 s each, 0.08 s apart from +0.40 s, no translate; landed
         words hold until the exit at +1.95 s.
SHOTS (global seconds):
  0.00-4.95   HOOK poster: mark + "Claim Assistant", "From claim form / to coverage call", a crop of the real
              handwritten form; teal boxes draw around Policy Number, name and accident date while a Key Fields
              card fills with POL 987654321 83%, Emily 79%, 2024-09-18 81% (real values and confidences).
  4.50-6.90   sheet "Pick the claim form" (the app is mounted under it from 6.4 s).
  6.90-11.95  toolbar at 2.4x: cursor to Form, menu opens, hover Florida handwritten, select, PDF crossfades
              (69% -> 73%), cursor to Process Form, hover, press: Processing..., Reset turns red.
  11.95-14.9  pull back to the whole app (1.333x): "Analyzing document..." spinner 2.4 s, results fade in,
              All 0 -> 54, Low confidence 0 -> 31.
  14.9-19.3   push to the Executive Summary (2.16x): callouts "Coverage call, with its reasons" (verdict
              badge "uncertain") and "54 fields read, 31 flagged".
  19.35-21.75 sheet "Values, traced back to the page".
  21.75-29.25 PDF + Key Fields (1.5x): hover Policy Number, box on "POL 987654321"; push 2.6x to the box,
              callout "Policy Number, read from here"; pull back, hover Loss Description, box on the
              description, callout "Values link back to their source".
  29.25-31.65 sheet "Fix what the model doubts".
  31.65-38.2  open Low Confidence Fields (31), scroll to COMPANY NAME "Pac Ecom Logistics" 36%, hover: the box
              lands on the D.B.A. line; callout "Company read from the D.B.A. line".
  38.2-45.3   push to the row (2.4x): Edit, click into the field, select all, type "Pacific E-Commerce
              Logistics, Inc.", Approve: bar fills emerald, "✓ 100%"; callout "Fixed, approved, now 100%".
  45.3-50.6   pull back (1.5x): approve the queue, three at normal speed, then 27 fast-forwarded (one per 0.1 s)
              as the list scrolls under the cursor; Export unlocks.
  50.6-54.3   scroll to top, push to the summary: "Reviewed: 31", callout "Export unlocks after review",
              hover and press Export.
  54.0-57.1   Export Ready dialog (real copy: "31 of 54 fields reviewed... ASC system"): push 2.4x from 54.2 s,
              the dialog fades in at 54.58 s once it is whole in frame; Confirm.
  57.15-59.4  pull back to the whole app, hold.
  58.90-66.40 end card (house B2): sheet whips in, the 220 px mark fills from the bottom (0.55-1.30 s),
              "Claim Assistant" (144 px, 111 px ink) wipes in (0.95-1.60 s), "Claim intake, read and
              reviewed." 46 px at 1.75 s, claim-assistant.symfa.ai 36 px at 2.15 s; landed by +2.45 s, held
              4.95 s; music fades 62.8-65.7 s, digital silence 65.7-66.4 s.
SOUND:   music bed (Lyria RealTime, 2 candidates; candidate 1, acoustic guitar + felt piano, ~97 BPM), low-passed
         at 12 kHz (Lyria high-band artefacts, 17-19 kHz), high-pass 35 Hz, -3 dB at 110 Hz, limiter at -1.5 dBFS;
         click-soft on every real click (0.9), quieter ticks on the fast-forwarded approvals (0.35), one typing
         burst under the typing (0.3), alternating whoosh takes on the sheet wipes (0.12-0.16). Nothing else.
BANNED:  persistent caption or subtitle strip; any hard content swap without a tween; error, empty-state, "N/A",
         dev-indicator or localhost text; spinners longer than 2.5 s; dark void ground; glow, particles,
         gradients; glass cards; three cards in a row; the logo docked in a corner; click rings; titles that
         drift after landing; left-aligned interstitial cards; `will-change` on the camera; 3D transforms.
QA:      frames every 2 s and +-0.2 s around every seam and zoom peak at full resolution; callout opacity only
         rises across consecutive frames; static labels identical across 10-frame holds; text >= 28 px for
         headlines and callouts; summary text matches capture.json; audio: no clipping (true peak <= -1 dBTP),
         silence in the last 0.5 s.
