# Claim Assistant demo film: storylines

Subject: Claim Assistant, the claim-intake tool (FastAPI + Azure Document Intelligence + OpenAI backend, Next.js
frontend). It reads a filled insurance claim form (PDF), extracts every field with a confidence score, matches the
claim to its policy record, writes a coverage summary with a verdict, and lets an adjuster review, correct and
approve fields before exporting the claim to the ASC system.

Viewer: a claims adjuster or intake lead who keys claim forms into a claims system by hand today.

One real piece of data travels through every option: the **Florida handwritten First Report of Injury** for
Emily Johnson (policy POL987654321), processed by the running backend (port 8010). Its real output: 54 fields,
31 flagged as low confidence, verdict **uncertain** (claimant/policy match 0.98), and one visible misread: the
company name came back as "Pac Ecom Logistics" (36%), read from the D.B.A. line instead of
"Pacific E-Commerce Logistics, Inc.".

---

## A. "One claim, start to export" (chosen)

- **Device / form:** a moment in an adjuster's day, told as one continuous take inside the product. Short headline
  sheets wipe across the app between chapters; inside a chapter the camera does the work.
- **What the viewer sees and feels:** a handwritten form goes in, a structured claim comes out. The adjuster picks
  the form, processes it, reads the coverage call, hovers fields to see where each value was read on the page,
  catches a real misread, fixes and approves it, clears the review queue and exports. It feels calm and in control:
  the tool does the reading, the human keeps the decision.
- **First two seconds:** a designed poster on the app's own #f8fafb ground: the shield mark and "Claim Assistant",
  the line "From claim form to coverage call", and a crop of the real handwritten form with the app's teal
  highlight boxes drawing around the name, the accident date and the policy number, each pulling its extracted
  value into a small Key Fields card.
- **Beats:** poster → "Pick the claim form" → Form menu, Florida handwritten, Process Form → results arrive,
  verdict and reasons, field counts → "Values, traced back to the page" → hover Policy Number and
  Loss Description, each boxed on the PDF → "Fix what the model doubts" → open Low Confidence Fields, hover
  Company Name (boxed on the D.B.A. line), edit, type the right name, approve → approve the queue, Reviewed counts
  to 31, Export unlocks → Export Ready dialog, Confirm Export → end card held while the music resolves.
- **Look:** the app's own system: #f8fafb ground, white cards with #e2e8f0 borders, slate ink, one teal accent
  (#0d9488) used for the highlight boxes, one word per headline and the callout rule; Plus Jakarta Sans only.
  Real UI at 1.33x to 2.4x.
- **Sound:** a light, warm acoustic-electronic bed at 96 BPM (bar = 2.5 s), soft clicks on real clicks, quiet
  key ticks while typing, a soft whoosh on each headline wipe; the music fades to silence under the end card.

**Why this one:** a stranger can follow it without narration. Every claim on screen is the product's own output for
one real form, including its doubt ("uncertain") and its mistake (the company name), which is exactly what the
review workflow exists for. The misread makes the review step feel necessary instead of decorative.

## B. "The misread"

- **Device / form:** the result first, then the pull-back.
- **What the viewer sees:** the film opens on one handwritten line filling the frame, "Pacific E-Commerce
  Logistics, Inc.", and the value the model read under it, "Pac Ecom Logistics", in rose at 36%. The camera pulls
  back: the value is a row in the Low Confidence queue, the queue sits under the coverage summary, the summary
  sits beside the form it was read from, and finally the whole app, where the adjuster fixes the row.
- **First two seconds:** the handwriting at 6x with a teal box drawing around the wrong line.
- **Beats:** misread → pull back to queue → to summary → to form → whole app → fix → approve → export → end card.
- **Look:** same app palette; one continuous zoom out.
- **Sound:** a single held note that opens into the bed as the camera pulls back.
- **Not chosen because:** it opens on the product's error. It is honest and striking, but a first-time viewer
  meets the tool through what it got wrong, and the main flow (pick a form, process, read the verdict) happens
  out of order or off camera.

## C. "Three questions an adjuster asks"

- **Device / form:** type carries the argument; each question is answered by a punch into the UI.
- **What the viewer sees:** "Is this claim covered?" → the verdict and summary; "Where did this number come from?"
  → hover a field, the box on the PDF; "Can I trust it?" → the confidence bars, the low-confidence queue and the
  approval that unlocks Export.
- **First two seconds:** "Is this claim covered?" typed in huge Plus Jakarta Sans on #f8fafb.
- **Beats:** Q1 → verdict → Q2 → source box → Q3 → review and export → end card.
- **Look:** white type planes alternating with the app.
- **Sound:** cuts on the beat, a riser into the export.
- **Not chosen because:** it drifts toward a kinetic-type slideshow, and type-to-UI cuts every 3 to 4 s leave too
  little time for believable interactions (the Form menu, the edit and the approval need 5 to 8 s each).

The chosen film borrows one thing from B (the misread is the heart of the review chapter) and one from C (the
headline sheets are short claims of 6 words or fewer).
