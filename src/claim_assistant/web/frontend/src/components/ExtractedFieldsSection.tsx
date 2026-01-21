import { useMemo, useState } from "react";

export type BoundingRegion = { page: number; polygon: number[] };

export type FieldRow = {
  order?: number;
  text?: string;
  alias?: string | null;
  answer?:
    | {
        value?: unknown;
        evidences?: Array<{
          confidence?: number | null;
          bounding_region?: BoundingRegion | null;
        }>;
      }
    | null; // <-- allow null
};

type Mode = "all" | "aliased";

type Props = {
  rows: FieldRow[];
  disabled?: boolean;
  onHoverRegion?: (region: BoundingRegion | null) => void;
};

type EvidenceType = NonNullable<FieldRow["answer"]>["evidences"];

function avgConfidence(evidences: EvidenceType | undefined): number | null {
  if (!evidences?.length) return null;
  const vals = evidences
    .map((e) => (typeof e?.confidence === "number" ? e.confidence : null))
    .filter((x): x is number => x !== null);
  if (!vals.length) return null;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function confidencePercent(field: FieldRow): string {
  const conf = avgConfidence(field.answer?.evidences);
  if (conf === null) return "—";
  return `${Math.round(conf * 100)}%`;
}

function renderFieldValue(field: FieldRow): string {
  const v = field.answer?.value;
  if (v === null || v === undefined) return "N/A";
  if (typeof v === "string" && v.trim() === "") return "N/A";
  return String(v);
}

function firstBoundingRegion(field: FieldRow): BoundingRegion | null {
  const br = field.answer?.evidences?.[0]?.bounding_region;
  if (!br) return null;
  if (typeof br.page !== "number") return null;
  if (!Array.isArray(br.polygon) || br.polygon.length !== 8) return null;
  return br;
}

export function ExtractedFieldsSection({ rows, disabled = false, onHoverRegion }: Props) {
  const [mode, setMode] = useState<Mode>("all");

  const filtered = useMemo(() => {
    return mode === "all" ? rows : rows.filter((r) => !!r.alias);
  }, [rows, mode]);

  return (
    <div style={{ marginBottom: 18 }}>
      <h3 style={{ margin: "12px 0 8px" }}>Extracted Fields</h3>

      {/* horizontal segmented selector */}
      <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 10 }}>
        <div style={{ display: "inline-flex", border: "1px solid #ddd", borderRadius: 999, overflow: "hidden" }}>
          <button
            type="button"
            disabled={disabled}
            onClick={() => setMode("all")}
            style={{
              border: 0,
              background: mode === "all" ? "rgba(34,187,102,0.14)" : "transparent",
              padding: "8px 12px",
              cursor: disabled ? "not-allowed" : "pointer",
              fontWeight: mode === "all" ? 700 : 400,
            }}
          >
            All
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={() => setMode("aliased")}
            style={{
              border: 0,
              background: mode === "aliased" ? "rgba(34,187,102,0.14)" : "transparent",
              padding: "8px 12px",
              cursor: disabled ? "not-allowed" : "pointer",
              fontWeight: mode === "aliased" ? 700 : 400,
            }}
          >
            Aliased only
          </button>
        </div>

        <span style={{ fontSize: 12, color: "#555", border: "1px solid #ddd", borderRadius: 999, padding: "2px 8px" }}>
          Hover row → highlight PDF
        </span>
      </div>

      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #eee" }}>Field</th>
            <th style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #eee" }}>Value</th>
            <th style={{ textAlign: "left", padding: "6px 8px", borderBottom: "1px solid #eee", width: 120 }}>
              Confidence
            </th>
          </tr>
        </thead>

        <tbody>
          {filtered.map((f) => {
            const key = String(f.order ?? f.text ?? Math.random());
            const region = firstBoundingRegion(f);

            return (
              <tr
                key={key}
                onMouseEnter={() => onHoverRegion?.(region)}
                onMouseLeave={() => onHoverRegion?.(null)}
                style={{ cursor: region ? "pointer" : "default" }}
              >
                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2", width: "45%" }}>
                  <div style={{ fontWeight: 600 }}>{String(f.text ?? "")}</div>
                  {f.alias ? (
                    <div style={{ marginTop: 6, display: "inline-block", padding: "2px 8px", border: "1px solid #ddd", borderRadius: 999, fontSize: 12 }}>
                      {String(f.alias)}
                    </div>
                  ) : null}
                </td>

                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2" }}>{renderFieldValue(f)}</td>

                <td style={{ padding: "6px 8px", borderBottom: "1px solid #f2f2f2" }}>{confidencePercent(f)}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
