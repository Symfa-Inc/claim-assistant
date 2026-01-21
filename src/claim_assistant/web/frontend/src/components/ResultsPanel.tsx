import { useState } from "react";
import { ExtractedFieldsSection, BoundingRegion } from "./ExtractedFieldsSection";
import { PdfViewer } from "./PdfViewer";
import type { CoverageAnalysisResponse } from "../types";

export function ResultsPanel(props: { analysis: CoverageAnalysisResponse; pdfUrl: string; processing?: boolean }) {
  const { analysis, pdfUrl, processing = false } = props;
  const [hoveredRegion, setHoveredRegion] = useState<BoundingRegion | null>(null);

  return (
    <div id="results" className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div>
        <PdfViewer pdfUrl={pdfUrl} highlight={hoveredRegion} />
      </div>

      <div className="space-y-4">
        <section className="rounded-2xl border bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Claim Analysis</h2>
          <div className="mt-2 text-sm">
            <div>
              <b>Conclusion:</b> {analysis.conclusion}
            </div>
            <div>
              <b>Confidence:</b> {Math.round((analysis.confidence ?? 0) * 100)}%
            </div>
          </div>
          <p className="mt-3 whitespace-pre-wrap text-sm text-gray-800">{analysis.executive_summary}</p>
        </section>

        <ExtractedFieldsSection rows={analysis.form ?? []} disabled={processing} onHoverRegion={setHoveredRegion} />

        <section className="rounded-2xl border bg-white p-4 shadow-sm">
          <h2 className="text-lg font-semibold">Policy Record</h2>
          {!analysis.policy ? (
            <div className="mt-2 text-sm text-gray-600">No policy record.</div>
          ) : (
            <div className="mt-2 text-sm">
              <div>
                <b>Policy #:</b> {analysis.policy.policy_number}
              </div>
              <div>
                <b>Holder:</b> {analysis.policy.policy_holder_first_name} {analysis.policy.policy_holder_last_name}
              </div>
              <div>
                <b>Start:</b> {analysis.policy.start_date}
              </div>
              <div>
                <b>End:</b> {analysis.policy.end_data}
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
