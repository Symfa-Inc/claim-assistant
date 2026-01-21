import { useEffect, useMemo, useRef, useState } from "react";

import type { CoverageAnalysisResponse } from "../types/index";
import type { RegistrySnapshot } from "../types/registry";
import { STATE_MAP, TYPE_MAP } from "../constants";
import { samplePdfUrl } from "../api";

import { PdfViewer } from "../components/PdfViewer";

// If you already have a ResultsPanel that renders the 3 sections + extracted fields modes + hover,
// you can switch to <ResultsPanel .../> inside the RESULTS area below.
// import { ResultsPanel } from "../components/ResultsPanel";

type SelectedMode =
  | { kind: "none" }
  | { kind: "sample"; sampleId: string; formCode: string; filename: string; pdfUrl: string }
  | { kind: "upload"; file: File; formCode: string };

type BoundingRegion = { page: number; polygon: number[] };

type FieldsMode = "all" | "aliased";

function Spinner() {
  return (
    <span style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
      <span
        style={{
          width: 14,
          height: 14,
          border: "2px solid #999",
          borderTopColor: "transparent",
          borderRadius: "50%",
          display: "inline-block",
          animation: "spin 0.8s linear infinite",
        }}
      />
      Processing…
    </span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ marginBottom: 18 }}>
      <h3 style={{ margin: "12px 0 8px" }}>{title}</h3>
      <div>{children}</div>
    </div>
  );
}

function KeyValueTable({ rows }: { rows: Array<[string, string]> }) {
  return (
    <table style={{ width: "100%", borderCollapse: "collapse" }}>
      <tbody>
        {rows.map(([k, v]) => (
          <tr key={k}>
            <td
              style={{
                width: 200,
                padding: "6px 8px",
                background: "#f5f5f5",
                verticalAlign: "top",
              }}
            >
              <strong>{k}</strong>
            </td>
            <td style={{ padding: "6px 8px", borderBottom: "1px solid #eee" }}>{v || "N/A"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function avgConfidence(evidences: any[] | undefined): number | null {
  if (!evidences || evidences.length === 0) return null;
  const vals: number[] = [];
  for (const e of evidences) {
    const c = typeof e?.confidence === "number" ? e.confidence : null;
    if (c !== null) vals.push(c);
  }
  if (vals.length === 0) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function confidencePercent(field: any): string {
  const conf = avgConfidence(field?.answer?.evidences);
  if (conf === null) return "—";
  return `${Math.round(conf * 100)}%`;
}

function renderFieldValue(field: any): string {
  const ans = field?.answer;
  if (!ans) return "N/A";
  const val = ans?.value;
  const valStr =
    val === null || val === undefined || (typeof val === "string" && val.trim() === "")
      ? "N/A"
      : String(val);

  return valStr;
}

function firstBoundingRegion(field: any): BoundingRegion | null {
  const ev = field?.answer?.evidences?.[0];
  const br = ev?.bounding_region;
  if (!br) return null;
  if (typeof br.page !== "number" || !Array.isArray(br.polygon)) return null;
  if (br.polygon.length !== 8) return null;
  return br as BoundingRegion;
}

function detectKindFromFilename(filename: string): string {
  // expects form_{hw|dg}_*.pdf (your samples look like that)
  const parts = filename.replace(".pdf", "").split("_");
  if (parts.length >= 3) {
    const t = parts[1];
    return TYPE_MAP[t as keyof typeof TYPE_MAP] ?? t;
  }
  return "Unknown";
}

export default function HomePage() {
  const [registry, setRegistry] = useState<RegistrySnapshot | null>(null);
  const [registryLoading, setRegistryLoading] = useState<boolean>(true);
  const [registryError, setRegistryError] = useState<string | null>(null);

  const [mode, setMode] = useState<"sample" | "upload">("sample");
  const [selection, setSelection] = useState<SelectedMode>({ kind: "none" });

  const [analysis, setAnalysis] = useState<CoverageAnalysisResponse | null>(null);
  const [processing, setProcessing] = useState(false);
  const [processError, setProcessError] = useState<string | null>(null);

  const resultsRef = useRef<HTMLDivElement | null>(null);

  // extracted fields UI
  const [fieldsMode, setFieldsMode] = useState<FieldsMode>("all");
  const [hoverRegion, setHoverRegion] = useState<BoundingRegion | null>(null);

  // ---------------------------
  // Load registry on page open
  // ---------------------------
  useEffect(() => {
    let cancelled = false;

    async function loadRegistry() {
      setRegistryLoading(true);
      setRegistryError(null);

      try {
        const resp = await fetch("/api/registry");
        if (!resp.ok) throw new Error(`Registry request failed: ${resp.status}`);
        const data = (await resp.json()) as RegistrySnapshot;

        if (!cancelled) {
          setRegistry(data);
          // set default upload form code if needed
          const firstCode = data.forms?.[0]?.code ?? "FL";
          if (selection.kind !== "upload") {
            // keep as-is; upload selection will set when file chosen
          } else {
            setSelection({ kind: "upload", file: selection.file, formCode: firstCode });
          }
        }
      } catch (e: any) {
        if (!cancelled) setRegistryError(e?.message ?? "Failed to load registry");
      } finally {
        if (!cancelled) setRegistryLoading(false);
      }
    }

    loadRegistry();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // ---------------------------
  // Derived data
  // ---------------------------
  const forms = registry?.forms ?? [];
  const samples = registry?.samples ?? [];

  const samplesByState = useMemo(() => {
    const grouped: Record<string, RegistrySnapshot["samples"]> = {};
    for (const s of samples) {
      (grouped[s.form_code] ??= []).push(s);
    }
    for (const k of Object.keys(grouped)) grouped[k].sort((a, b) => a.filename.localeCompare(b.filename));
    return grouped;
  }, [samples]);

  // pdf url for viewer
  const pdfUrl = useMemo(() => {
    if (selection.kind === "sample") return selection.pdfUrl;
    if (selection.kind === "upload") return URL.createObjectURL(selection.file);
    return null;
  }, [selection]);

  // cleanup object URL (upload only)
  useEffect(() => {
    return () => {
      if (selection.kind === "upload" && pdfUrl && pdfUrl.startsWith("blob:")) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [selection, pdfUrl]);

  const canProcess =
    !processing &&
    ((mode === "sample" && selection.kind === "sample") || (mode === "upload" && selection.kind === "upload"));

  // ---------------------------
  // Handlers
  // ---------------------------
  function onSelectSample(sample: RegistrySnapshot["samples"][number]) {
    setAnalysis(null);
    setProcessError(null);
    setHoverRegion(null);

    setMode("sample");
    setSelection({
      kind: "sample",
      sampleId: sample.id,
      formCode: sample.form_code,
      filename: sample.filename,
      pdfUrl: samplePdfUrl(sample.id),
    });
  }

  function onUploadFile(file: File | null) {
    setAnalysis(null);
    setProcessError(null);
    setHoverRegion(null);

    setMode("upload");

    if (!file) {
      setSelection({ kind: "none" });
      return;
    }

    const defaultFormCode = forms?.[0]?.code ?? "FL";
    setSelection({ kind: "upload", file, formCode: defaultFormCode });
  }

  function onUploadFormCodeChange(newCode: string) {
    if (selection.kind !== "upload") return;
    setAnalysis(null);
    setProcessError(null);
    setHoverRegion(null);

    setSelection({ kind: "upload", file: selection.file, formCode: newCode });
  }

  async function onProcessClick() {
    if (!canProcess) return;

    setAnalysis(null);
    setProcessError(null);
    setHoverRegion(null);
    setProcessing(true);

    try {
      let resp: Response;

      if (mode === "sample") {
        if (selection.kind !== "sample") throw new Error("Please select a sample.");
        const body = new URLSearchParams();
        body.set("sample_id", selection.sampleId);

        resp = await fetch("/api/process-sample", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body,
        });
      } else {
        if (selection.kind !== "upload") throw new Error("Please upload a PDF file.");
        const fd = new FormData();
        fd.set("form_type", selection.formCode);
        fd.set("file", selection.file);

        resp = await fetch("/api/process", {
          method: "POST",
          body: fd,
        });
      }

      if (!resp.ok) {
        let msg = `Processing failed (${resp.status})`;
        try {
          const j = await resp.json();
          if (j?.detail) msg = String(j.detail);
        } catch {
          // ignore
        }
        throw new Error(msg);
      }

      const data = (await resp.json()) as CoverageAnalysisResponse;
      setAnalysis(data);

      requestAnimationFrame(() => {
        resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } catch (e: any) {
      setProcessError(e?.message ?? "Processing error");
    } finally {
      setProcessing(false);
    }
  }

  // ---------------------------
  // Render
  // ---------------------------
  if (registryLoading && !registry) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Claim Assistant</h2>
        <p>Loading registry…</p>
      </div>
    );
  }

  if (registryError && !registry) {
    return (
      <div style={{ padding: 20 }}>
        <h2>Claim Assistant</h2>
        <p style={{ color: "crimson" }}>{registryError}</p>
      </div>
    );
  }

  return (
    <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto" }}>
      <style>
        {`
          @keyframes spin { to { transform: rotate(360deg); } }

          .card { border: 1px solid #e5e5e5; border-radius: 12px; padding: 12px; background: #fff; }
          .btn { border: 1px solid #ccc; background: white; padding: 10px 14px; border-radius: 10px; cursor: pointer; }
          .btnPrimary { border: 1px solid #2b6; background: #2b6; color: white; }
          .btn:disabled { opacity: 0.55; cursor: not-allowed; }

          .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
          .row { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
          .pill { display: inline-block; padding: 2px 8px; border: 1px solid #ddd; border-radius: 999px; font-size: 12px; color: #444; }

          .seg { display: inline-flex; border: 1px solid #ddd; border-radius: 999px; overflow: hidden; }
          .seg button { border: 0; background: transparent; padding: 8px 12px; cursor: pointer; }
          .seg button.active { background: rgba(34,187,102,0.14); font-weight: 700; }

          .err { border: 1px solid #f5c2c7; background: #f8d7da; color: #842029; padding: 10px 12px; border-radius: 10px; }
        `}
      </style>

      <h1 style={{ marginBottom: 6 }}>Process Claim Form</h1>
      <p style={{ marginTop: 0, color: "#444" }}>
        Choose an example form or upload your own PDF to begin processing.
      </p>

      {registryError && <div className="err" style={{ marginBottom: 12 }}>{registryError}</div>}

      {/* Mode switch (central block style) */}
      <div className="card" style={{ marginBottom: 14 }}>
        <div className="row">
          <label>
            <input
              type="radio"
              checked={mode === "sample"}
              onChange={() => {
                setMode("sample");
                setAnalysis(null);
                setProcessError(null);
                setHoverRegion(null);
              }}
            />{" "}
            Use sample
          </label>

          <label>
            <input
              type="radio"
              checked={mode === "upload"}
              onChange={() => {
                setMode("upload");
                setAnalysis(null);
                setProcessError(null);
                setHoverRegion(null);
              }}
            />{" "}
            Upload PDF
          </label>
        </div>
      </div>

      {/* SAMPLE MODE */}
      {mode === "sample" && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h2 style={{ marginTop: 0 }}>Example Forms</h2>

          {Object.entries(samplesByState)
            .sort(([a], [b]) => a.localeCompare(b))
            .map(([state, stateSamples]) => (
              <div key={state} style={{ marginBottom: 14 }}>
                <h3 style={{ marginBottom: 8 }}>
                  {STATE_MAP[state as keyof typeof STATE_MAP] ?? state} <span className="pill">{state}</span>
                </h3>

                <div className="grid2">
                  {stateSamples.map((s) => {
                    const selected = selection.kind === "sample" && selection.sampleId === s.id;
                    const kind = detectKindFromFilename(s.filename);

                    return (
                      <button
                        key={s.id}
                        className="btn"
                        style={{
                          textAlign: "left",
                          borderColor: selected ? "#2b6" : "#ddd",
                          background: selected ? "rgba(34,187,102,0.08)" : "white",
                        }}
                        disabled={processing}
                        onClick={() => onSelectSample(s)}
                      >
                        <div style={{ fontWeight: 700 }}>{s.filename}</div>
                        <div style={{ color: "#555", marginTop: 4 }}>{kind}</div>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
        </div>
      )}

      {/* UPLOAD MODE */}
      {mode === "upload" && (
        <div className="card" style={{ marginBottom: 14 }}>
          <h2 style={{ marginTop: 0 }}>Upload Custom PDF</h2>

          <div className="row" style={{ marginBottom: 10 }}>
            <input
              type="file"
              accept="application/pdf"
              disabled={processing}
              onChange={(e) => onUploadFile(e.target.files?.[0] ?? null)}
            />

            <label style={{ display: "inline-flex", gap: 8, alignItems: "center" }}>
              Form type:
              <select
                value={selection.kind === "upload" ? selection.formCode : (forms?.[0]?.code ?? "FL")}
                disabled={processing}
                onChange={(e) => onUploadFormCodeChange(e.target.value)}
              >
                {forms.map((f) => (
                  <option key={f.code} value={f.code}>
                    {(STATE_MAP as any)[f.code] ?? f.label ?? f.code}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selection.kind === "upload" && <div className="pill">Ready: {selection.file.name}</div>}
        </div>
      )}

      {/* Process button */}
      <div className="row" style={{ marginBottom: 14 }}>
        <button className="btn btnPrimary" disabled={!canProcess} onClick={onProcessClick}>
          {processing ? <Spinner /> : "Process Form"}
        </button>

        {processError && <span style={{ color: "crimson" }}>{processError}</span>}
      </div>

      {/* RESULTS (hidden until analysis exists) */}
      {analysis && pdfUrl && (
        <div ref={resultsRef} className="card" style={{ marginTop: 18 }}>
          <h2 style={{ marginTop: 0 }}>Results</h2>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1.2fr", gap: 14 }}>
            {/* LEFT: PDF */}
            <div className="card" style={{ padding: 10 }}>
              <h3 style={{ marginTop: 0 }}>Input PDF</h3>
              <PdfViewer pdfUrl={pdfUrl} highlight={hoverRegion} height={720} />
            </div>

            {/* RIGHT: Analysis */}
            <div className="card" style={{ padding: 10 }}>
              <Section title="Claim Analysis">
                <KeyValueTable
                  rows={[
                    ["Conclusion", String(analysis.conclusion ?? "N/A")],
                    [
                      "Confidence",
                      typeof analysis.confidence === "number"
                        ? `${Math.round(analysis.confidence * 100)}%`
                        : "N/A",
                    ],
                    ["Executive summary", String(analysis.executive_summary ?? "N/A")],
                  ]}
                />
              </Section>

              <Section title="Extracted Fields">
                {/* horizontal selector */}
                <div className="row" style={{ marginBottom: 10 }}>
                  <div className="seg">
                    <button
                      type="button"
                      className={fieldsMode === "all" ? "active" : ""}
                      onClick={() => setFieldsMode("all")}
                    >
                      All
                    </button>
                    <button
                      type="button"
                      className={fieldsMode === "aliased" ? "active" : ""}
                      onClick={() => setFieldsMode("aliased")}
                    >
                      Aliased only
                    </button>
                  </div>
                  <span className="pill">Hover row → highlight PDF</span>
                </div>

                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #eee" }}>
                        Field
                      </th>
                      <th style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #eee" }}>
                        Value
                      </th>
                      <th
                        style={{
                          textAlign: "left",
                          padding: "6px 8px",
                          borderBottom: "1px solid #eee",
                          width: 120,
                        }}
                      >
                        Confidence
                      </th>
                    </tr>
                  </thead>

                  <tbody>
                    {(analysis.form ?? [])
                      .filter((f: any) => (fieldsMode === "all" ? true : !!f.alias))
                      .map((f: any) => {
                        const key = String(f.order ?? f.text);
                        const br = firstBoundingRegion(f);

                        return (
                          <tr
                            key={key}
                            onMouseEnter={() => setHoverRegion(br)}
                            onMouseLeave={() => setHoverRegion(null)}
                            style={{ cursor: br ? "pointer" : "default" }}
                          >
                            <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2", width: "45%" }}>
                              <div style={{ fontWeight: 600 }}>{String(f.text ?? "")}</div>
                              {f.alias ? (
                                <div className="pill" style={{ marginTop: 6 }}>
                                  {String(f.alias)}
                                </div>
                              ) : null}
                            </td>

                            <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2" }}>
                              {renderFieldValue(f)}
                            </td>

                            <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2" }}>
                              {confidencePercent(f)}
                            </td>
                          </tr>
                        );
                      })}
                  </tbody>
                </table>
              </Section>

              <Section title="Matched Policy Record">
                {analysis.policy ? (
                  <KeyValueTable
                    rows={[
                      ["Policy number", String((analysis.policy as any).policy_number ?? "N/A")],
                      [
                        "Policy holder",
                        `${String((analysis.policy as any).policy_holder_first_name ?? "")} ${String(
                          (analysis.policy as any).policy_holder_last_name ?? "",
                        )}`.trim() || "N/A",
                      ],
                      ["Coverage start", String((analysis.policy as any).start_date ?? "N/A")],
                      ["Coverage end", String((analysis.policy as any).end_date ?? (analysis.policy as any).end_data ?? "N/A")],
                      ["Policy file", String((analysis.policy as any).policy_file_name ?? "N/A")],
                    ]}
                  />
                ) : (
                  <p>Policy not found.</p>
                )}
              </Section>

              {/* If you prefer: replace everything on the RIGHT with your existing component:
                  <ResultsPanel analysis={analysis} pdfUrl={pdfUrl} />
                  and delete the right-side markup above.
               */}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
