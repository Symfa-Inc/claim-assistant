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
  const [initialFieldState, setInitialFieldState] = useState<
    Record<string, { value: string; confidence: string }>
  >({});

  const parseConfidence = (confidence: string): number => {
    const value = parseFloat(confidence);
    return Number.isNaN(value) ? 0 : value;
  };

  const mapAndUpdateFields = (
    fields: ClaimField[],
    fieldId: string,
    updater: (field: ClaimField) => ClaimField,
  ) => fields.map((field) => (field.id === fieldId ? updater(field) : field));

  const handleFieldValueChange = (fieldId: string, value: string) => {
    setClaimFields((current) =>
      mapAndUpdateFields(current, fieldId, (field) => ({
        ...field,
        value,
      })),
    );
    setKeyClaimFields((current) =>
      mapAndUpdateFields(current, fieldId, (field) => ({
        ...field,
        value,
      })),
    );
  };

  const handleFieldApprove = (fieldId: string) => {
    const currentField = claimFields.find((field) => field.id === fieldId);
    if (!currentField) return;

    const shouldValidate = !currentField.validated;
    const initial = initialFieldState[fieldId];
    const updatedField = (field: ClaimField): ClaimField => {
      if (shouldValidate) {
        return {
          ...field,
          validated: true,
          confidence: '100%',
        };
      }
      return {
        ...field,
        value: initial?.value ?? field.value,
        confidence: initial?.confidence ?? field.confidence,
        validated: false,
      };
    };

    setClaimFields((current) => mapAndUpdateFields(current, fieldId, updatedField));
    setKeyClaimFields((current) => mapAndUpdateFields(current, fieldId, updatedField));
  };

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
    setClaimFields(fields.map((field) => ({ ...field, validated: false })));
    setKeyClaimFields(keyFields.map((field) => ({ ...field, validated: false })));
    setInitialFieldState(
      fields.reduce<Record<string, { value: string; confidence: string }>>(
        (acc, field) => {
          acc[field.id] = {
            value: field.value,
            confidence: field.confidence,
          };
          return acc;
        },
        {},
      ),
    );
    setHighlightBoxes(boxes);
    setExecutiveSummary(summary?.executiveSummary ?? null);
    setSummaryConfidence(summary?.confidence ?? null);
    setSummaryConclusion(summary?.conclusion ?? null);
    setIsProcessing(false);
    setShowTable(true);
  };

  const handleReset = () => {
    setClaimFields([]);
    setKeyClaimFields([]);
    setHighlightBoxes([]);
    setExecutiveSummary(null);
    setSummaryConfidence(null);
    setSummaryConclusion(null);
    setInitialFieldState({});
    setHoveredFieldId(null);
    setIsProcessing(false);
    setShowTable(false);
  };

  const lowConfidenceFields = claimFields.filter(
    (field) => parseConfidence(initialFieldState[field.id]?.confidence ?? field.confidence) < 80,
  );
  const reviewedFieldsCount = claimFields.filter((field) => field.validated).length;
  const totalFieldsCount = claimFields.length;
  const lowConfidenceFieldIds = new Set(lowConfidenceFields.map((field) => field.id));
  const lowConfidenceFieldsCount = lowConfidenceFields.length;
  const reviewedLowConfidenceFieldsCount = claimFields.filter(
    (field) => lowConfidenceFieldIds.has(field.id) && field.validated,
  ).length;
  const hasUnreviewedLowConfidenceFields =
    lowConfidenceFieldsCount > 0 && reviewedLowConfidenceFieldsCount < lowConfidenceFieldsCount;
  const rightPanelClassName =
    'flex flex-1 self-start flex-col md:w-2/4 md:sticky md:top-[5.25rem] md:max-h-[calc(100vh-6.25rem)]';

  return (
    <main className="flex min-h-screen flex-col bg-slate-50">
      {/* Modern header with glass effect */}
      <header className="sticky top-0 z-50 border-b border-white/20 bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-700 text-white shadow-lg shadow-indigo-500/20">
        <div className="mx-auto px-6 py-4">
          <h1 className="text-2xl font-bold tracking-tight">
            Claim Assistant
          </h1>
        </div>
      </header>

      <div className="mx-4 flex flex-1 flex-col items-start gap-5 py-5 md:mx-6 md:flex-row">
        {/* Left panel - PDF Viewer */}
        <div className="flex flex-1 items-stretch md:w-2/4">
          <div className="bg-white card-shadow card-shadow-hover flex w-full flex-1 flex-col rounded-2xl border border-slate-200/60 p-5 transition-all">
            <AppPdfViewer
              isProcessing={isProcessing}
              onProcess={handleProcess}
              onProcessed={handleProcessed}
              onReset={handleReset}
              highlightFieldId={showTable ? hoveredFieldId : null}
              highlightBoxes={highlightBoxes}
            />
          </div>
        </div>

        {/* Right panel - Results */}
        {isProcessing ? (
          <div className={rightPanelClassName}>
            <div className="glass-card card-shadow flex flex-1 flex-col rounded-2xl border border-slate-200/60 p-6">
              <div className="flex flex-1 flex-col items-center justify-center gap-4 text-slate-600">
                <div className="relative">
                  <div className="h-12 w-12 animate-spin rounded-full border-[3px] border-slate-200 border-t-indigo-600" />
                  <div className="absolute inset-0 h-12 w-12 animate-ping rounded-full border-2 border-indigo-400 opacity-20" />
                </div>
                <span className="text-sm font-medium text-slate-500">Analyzing document...</span>
              </div>
            </div>
          </div>
        ) : showTable ? (
          <div className={`${rightPanelClassName} gap-4 overflow-y-auto pr-1`}>
            {/* Executive Summary Card */}
            <div className="bg-white card-shadow card-shadow-hover rounded-2xl border border-slate-200/60 px-6 py-5 transition-all">
              <details open>
                <summary className="cursor-pointer select-none pl-5">
                  <div className="ml-2 inline-flex w-[calc(100%-1.5rem)] items-center justify-between gap-3">
                    <span className="text-base font-semibold text-slate-800">
                      Executive Summary
                    </span>
                    <button
                      type="button"
                      onClick={(e) => e.stopPropagation()}
                      disabled={hasUnreviewedLowConfidenceFields}
                      aria-disabled={hasUnreviewedLowConfidenceFields}
                      className={`inline-flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium shadow-sm transition-all ${
                        hasUnreviewedLowConfidenceFields
                          ? 'cursor-not-allowed border-slate-200 bg-slate-100 text-slate-400'
                          : 'btn-primary border-transparent text-white'
                      }`}
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      Export to ASC
                    </button>
                  </div>
                </summary>
                {executiveSummary ? (
                  <div className="mt-4 max-w-full pl-5">
                    <table className="w-full table-fixed text-left text-sm text-slate-600">
                      <tbody className="divide-y divide-slate-100">
                        <tr>
                          <td className="py-3 pr-4 font-medium text-slate-700 w-32 align-top">
                            Summary
                          </td>
                          <td className="py-3 break-words text-justify leading-relaxed">{executiveSummary}</td>
                        </tr>
                        {summaryConclusion && (
                          <tr>
                            <td className="py-3 pr-4 font-medium text-slate-700 w-32">
                              Conclusion
                            </td>
                            <td
                              className={`py-3 break-words ${summaryConclusion.toLowerCase() === 'positive'
                                ? 'text-emerald-600'
                                : summaryConclusion.toLowerCase() === 'negative'
                                  ? 'text-rose-600'
                                  : 'text-amber-600'
                                } font-semibold uppercase tracking-wide`}
                            >
                              <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs ${
                                summaryConclusion.toLowerCase() === 'positive'
                                  ? 'bg-emerald-50 text-emerald-700'
                                  : summaryConclusion.toLowerCase() === 'negative'
                                    ? 'bg-rose-50 text-rose-700'
                                    : 'bg-amber-50 text-amber-700'
                              }`}>
                                <span className={`h-1.5 w-1.5 rounded-full ${
                                  summaryConclusion.toLowerCase() === 'positive'
                                    ? 'bg-emerald-500'
                                    : summaryConclusion.toLowerCase() === 'negative'
                                      ? 'bg-rose-500'
                                      : 'bg-amber-500'
                                }`} />
                                {summaryConclusion}
                              </span>
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                    <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-1 font-medium text-slate-600">
                        All: {totalFieldsCount}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-1 font-medium text-amber-700">
                        Low confidence: {lowConfidenceFieldsCount}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2 py-1 font-medium text-emerald-700">
                        Reviewed: {reviewedFieldsCount}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 pl-5 text-sm text-slate-400">
                    No executive summary available.
                  </div>
                )}
              </details>
            </div>

            {/* Key Fields Card */}
            <div className="bg-white card-shadow card-shadow-hover rounded-2xl border border-slate-200/60 px-6 py-5 transition-all">
              <details open>
                <summary className="cursor-pointer select-none pl-5 text-base font-semibold text-slate-800">
                  <span className="ml-2">Key Fields</span>
                </summary>
                <div className="mt-4 pl-5">
                  <ClaimTable
                    fields={keyClaimFields}
                    activeFieldId={hoveredFieldId}
                    onHover={setHoveredFieldId}
                    onFieldValueChange={handleFieldValueChange}
                    onFieldApprove={handleFieldApprove}
                    className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                  />
                </div>
              </details>
            </div>

            {/* Low Confidence Fields Card */}
            <div className="bg-white card-shadow card-shadow-hover rounded-2xl border border-slate-200/60 px-6 py-5 transition-all">
              <details>
                <summary className="cursor-pointer select-none pl-5 text-base font-semibold text-slate-800">
                  <span className="ml-2">Low Confidence Fields</span>
                </summary>
                <div className="mt-4 pl-5">
                  <ClaimTable
                    fields={lowConfidenceFields}
                    activeFieldId={hoveredFieldId}
                    onHover={setHoveredFieldId}
                    onFieldValueChange={handleFieldValueChange}
                    onFieldApprove={handleFieldApprove}
                    emptyMessage="No low confidence fields below 80%."
                    className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                  />
                </div>
              </details>
            </div>

            {/* All Fields Card */}
            <div className="bg-white card-shadow card-shadow-hover rounded-2xl border border-slate-200/60 px-6 py-5 transition-all">
              <details>
                <summary className="cursor-pointer select-none pl-5 text-base font-semibold text-slate-800">
                  <span className="ml-2">All Fields</span>
                </summary>
                <div className="mt-4 pl-5">
                  <ClaimTable
                    fields={claimFields}
                    activeFieldId={hoveredFieldId}
                    onHover={setHoveredFieldId}
                    onFieldValueChange={handleFieldValueChange}
                    onFieldApprove={handleFieldApprove}
                    className="flex min-h-0 flex-1 flex-col bg-transparent p-0 md:w-full"
                  />
                </div>
              </details>
            </div>
          </div>
        ) : (
          <div className={rightPanelClassName}>
            <div className="glass-card card-shadow flex flex-1 flex-col rounded-2xl border border-slate-200/60 p-6">
              <div className="flex flex-1 flex-col items-center justify-center gap-3">
                <div className="rounded-full bg-slate-100 p-4">
                  <svg className="h-8 w-8 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <p className="text-sm text-slate-500">
                  Upload a PDF and click <span className="font-medium text-slate-700">"Process Form"</span> to view extracted fields.
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
