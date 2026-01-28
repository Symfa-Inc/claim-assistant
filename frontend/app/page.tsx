'use client'


import { useState } from 'react';
import dynamic from 'next/dynamic';
import ClaimTable, { type ClaimField } from '@/app/ui/components/claim-table';
import type { HighlightBox } from '@/app/ui/components/pdf-viewer';

const AppPdfViewer = dynamic(() => import('@/app/ui/components/pdf-viewer'), {
  ssr: false,
});

export default function Page() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [showTable, setShowTable] = useState(false);
  const [hoveredFieldId, setHoveredFieldId] = useState<string | null>(null);
  const [claimFields, setClaimFields] = useState<ClaimField[]>([]);
  const [keyClaimFields, setKeyClaimFields] = useState<ClaimField[]>([]);
  const [highlightBoxes, setHighlightBoxes] = useState<HighlightBox[]>([]);
  const [executiveSummary, setExecutiveSummary] = useState<string | null>(null);
  const [summaryConfidence, setSummaryConfidence] = useState<number | null>(null);
  const [summaryConclusion, setSummaryConclusion] = useState<string | null>(null);

  const handleProcess = () => {
    if (isProcessing) return;
    setShowTable(false);
    setIsProcessing(true);
    setHighlightBoxes([]);
    setExecutiveSummary(null);
    setSummaryConfidence(null);
    setSummaryConclusion(null);
  };

  const handleProcessed = (
    fields: ClaimField[],
    keyFields: ClaimField[],
    boxes: HighlightBox[],
    summary: {
      executiveSummary: string;
      confidence: number | null;
      conclusion: string | null;
    } | null,
  ) => {
    setClaimFields(fields);
    setKeyClaimFields(keyFields);
    setHighlightBoxes(boxes);
    setExecutiveSummary(summary?.executiveSummary ?? null);
    setSummaryConfidence(summary?.confidence ?? null);
    setSummaryConclusion(summary?.conclusion ?? null);
    setIsProcessing(false);
    setShowTable(true);
  };

  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      <header className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-sm">
        <div className="mx-auto px-4 py-4 text-2xl font-semibold">
          Claim Assistant
        </div>
      </header>
      <div className="mx-4 flex flex-1 flex-col gap-4 py-4 md:flex-row">
        <div className="flex flex-1 items-stretch md:w-2/4 md:px-0">
          <div className="flex w-full flex-1 flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <AppPdfViewer
              isProcessing={isProcessing}
              onProcess={handleProcess}
              onProcessed={handleProcessed}
              highlightFieldId={showTable ? hoveredFieldId : null}
              highlightBoxes={highlightBoxes}
            />
          </div>
        </div>
        {isProcessing ? (
          <div className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:w-2/4">
            <div className="mt-6 flex flex-1 flex-col items-center justify-center gap-3 text-slate-600">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-blue-600" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          </div>
        ) : showTable ? (
          <div className="flex flex-1 flex-col gap-4 md:w-2/4">
            <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-lg font-semibold text-slate-800">
                  Executive Summary
                </h3>
                <button
                  type="button"
                  className="rounded-md shrink-0 whitespace-nowrap px-3 py-1 text-sm font-medium text-white shadow-sm bg-emerald-600 hover:bg-emerald-600"
                >
                  Export to AEC
                </button>
              </div>
              {executiveSummary ? (
                <div className="mt-2 max-w-full">
                  <table className="w-full table-fixed text-left text-sm text-slate-700">
                    <tbody className="divide-y divide-slate-100">
                      <tr>
                        <td className="py-3 pr-12 font-medium text-slate-800 w-56">
                          Summary
                        </td>
                        <td className="py-3 break-words">{executiveSummary}</td>
                      </tr>
                      {summaryConclusion && (
                        <tr>
                          <td className="py-3 pr-12 font-medium text-slate-800 w-96">
                            Conclusion
                          </td>
                          <td
                            className={`py-3 break-words ${summaryConclusion.toLowerCase() === 'positive'
                              ? 'text-green-600'
                              : summaryConclusion.toLowerCase() === 'negative'
                                ? 'text-red-600'
                                : 'text-slate-700'
                              } font-semibold uppercase tracking-wide`}
                          >
                            {summaryConclusion}
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="mt-2 text-sm text-slate-500">
                  No executive summary available.
                </div>
              )}
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
              <h3 className="text-lg font-semibold text-slate-800">
                Key Claim Fields
              </h3>
              <div className="mt-2">
                <ClaimTable
                  fields={keyClaimFields}
                  activeFieldId={hoveredFieldId}
                  onHover={setHoveredFieldId}
                  className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                />
              </div>
            </div>
            <div className="rounded-xl border border-slate-200 bg-white px-6 py-4 shadow-sm">
              <details>
                <summary className="cursor-pointer text-lg font-semibold text-slate-800">
                  All Fields
                </summary>
                <div className="mt-2 max-h-96 overflow-auto">
                  <ClaimTable
                    fields={claimFields}
                    activeFieldId={hoveredFieldId}
                    onHover={setHoveredFieldId}
                    className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                  />
                </div>
              </details>
            </div>
          </div>
        ) : (
          <div className="flex flex-1 flex-col rounded-xl border border-slate-200 bg-white p-6 shadow-sm md:w-2/4">
            <div className="mt-6 flex flex-1 flex-col items-center justify-center text-sm text-slate-500">
              Upload a PDF and click “Process PDF” to view extracted fields.
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
