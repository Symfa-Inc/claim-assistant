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
    <main className="flex min-h-screen flex-col">
      <header className="bg-blue-600 text-white">
        <div className="mx-auto px-4 py-4 text-2xl font-semibold">
          Claim Assistant
        </div>
      </header>
      <div className="ml-4 mr-4 flex flex-1 flex-col gap-4 py-4 md:flex-row">
        <div className="flex flex-1 items-stretch md:w-2/4 md:px-0">
          <div className="flex w-full flex-1 flex-col rounded-lg bg-gray-50 p-4">
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
          <div className="flex flex-1 flex-col rounded-lg bg-gray-50 p-4 md:w-2/4 md:px-10">
            <div className="mt-6 flex flex-1 flex-col items-center justify-center gap-3 text-gray-600">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          </div>
        ) : showTable ? (
          <div className="rounded-lg bg-gray-50 px-6 py-4 md:w-2/4">
            {executiveSummary && (
              <div>
                <details open>
                  <summary className="flex list-item items-center justify-between gap-3 cursor-pointer text-lg font-semibold text-gray-800">
                    <span>Executive Summary</span>
                    {/* <button
                      type="button"
                      className="rounded-md bg-green-600 px-3 py-1 text-sm text-white hover:bg-green-600"
                    >
                      Export to AEC
                    </button> */}
                  </summary>
                  <div className="mt-2 overflow-auto max-w-full">
                    <table className="w-full table-fixed text-left text-sm text-gray-700">
                      <tbody className="divide-y divide-gray-200">
                        <tr>
                          <td className="py-3 pr-12 font-medium text-gray-800 w-96">
                            Summary
                          </td>
                          <td className="py-3 break-words">{executiveSummary}</td>
                        </tr>
                        {typeof summaryConfidence === 'number' && (
                          <tr>
                            <td className="py-3 pr-12 font-medium text-gray-800 w-96">
                              Confidence
                            </td>
                            <td className="py-3">
                              {Math.round(summaryConfidence * 100)}%
                            </td>
                          </tr>
                        )}
                        {summaryConclusion && (
                          <tr>
                            <td className="py-3 pr-12 font-medium text-gray-800 w-96">
                              Conclusion
                            </td>
                            <td className="py-3 break-words">
                              {summaryConclusion}
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </details>
              </div>
            )}
            <div className="mt-4">
              <details open>
                <summary className="cursor-pointer text-lg font-semibold text-gray-800">
                  Key Claim Fields
                </summary>
                <div className="mt-2 max-h-96 overflow-auto">
                  <ClaimTable
                    fields={keyClaimFields}
                    activeFieldId={hoveredFieldId}
                    onHover={setHoveredFieldId}
                    className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                  />
                </div>
              </details>
            </div>
            <div className="mt-4">
              <details>
                <summary className="cursor-pointer text-lg font-semibold text-gray-800">
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
          <div className="flex flex-1 flex-col rounded-lg bg-gray-50 p-4 md:w-2/4 md:px-10">
            <div className="mt-6 flex flex-1 flex-col items-center justify-center text-sm text-gray-500">
              Upload a PDF and click “Process PDF” to view extracted fields.
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
