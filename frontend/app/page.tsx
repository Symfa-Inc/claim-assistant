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
    'flex flex-1 self-start flex-col md:w-2/4 md:sticky md:top-[4rem] md:max-h-[calc(100vh-5rem)]';

  const conclusionLower = summaryConclusion?.toLowerCase();
  const conclusionBadge =
    conclusionLower === 'positive'
      ? 'bg-emerald-50 text-emerald-700'
      : conclusionLower === 'negative'
        ? 'bg-rose-50 text-rose-700'
        : 'bg-amber-50 text-amber-700';
  const conclusionDot =
    conclusionLower === 'positive'
      ? 'bg-emerald-500'
      : conclusionLower === 'negative'
        ? 'bg-rose-500'
        : 'bg-amber-500';

  return (
    <main className="flex min-h-screen flex-col bg-[#f8fafb]">
      {/* ── Header ──────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex items-center gap-3.5 px-6 py-2.5">
          <div className="h-8 w-1 rounded-full bg-accent" />
          <div>
            <h1 className="text-[17px] font-bold tracking-tight text-slate-900">
              Claim Assistant
            </h1>
            <p className="text-[11px] leading-tight text-slate-400">
              Automate insurance claim intake with intelligent field extraction and mapping
            </p>
          </div>
        </div>
      </header>

      <div className="mx-4 flex flex-1 flex-col items-start gap-5 py-5 md:mx-6 md:flex-row">
        {/* ── Left panel – PDF Viewer ────────────── */}
        <div className="flex min-w-0 flex-1 items-stretch md:w-2/4">
          <div className="card flex w-full min-w-0 flex-1 flex-col overflow-hidden p-2.5">
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

        {/* ── Right panel – Results ──────────────── */}
        {isProcessing ? (
          <div className={rightPanelClassName}>
            <div className="card flex flex-1 flex-col items-center justify-center p-6">
              <div className="h-10 w-10 animate-spin rounded-full border-[2.5px] border-slate-200 border-t-accent" />
              <span className="mt-4 text-[13px] text-slate-400">Analyzing document...</span>
            </div>
          </div>
        ) : showTable ? (
          <div className={`${rightPanelClassName} gap-4 overflow-y-auto pb-14 pr-1`}>

            {/* Executive Summary */}
            <div
              className="card relative z-30 border-l-[3px] border-l-accent px-6 py-5 animate-fade-in"
              style={{ opacity: 0 }}
            >
              <details open>
                <summary className="cursor-pointer select-none pl-5">
                  <div className="ml-2 inline-flex w-[calc(100%-1.5rem)] items-center justify-between gap-3">
                    <span className="text-[15px] font-semibold text-slate-800 inline-flex items-center gap-2">
                      Executive Summary
                      <span className="info-tip info-tip-down" data-tip="Automated analysis highlighting key findings, confidence levels, and an overall claim conclusion">i</span>
                    </span>
                    <button
                      type="button"
                      onClick={(e) => e.stopPropagation()}
                      disabled={hasUnreviewedLowConfidenceFields}
                      aria-disabled={hasUnreviewedLowConfidenceFields}
                      className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-[13px] font-medium transition-all ${
                        hasUnreviewedLowConfidenceFields
                          ? 'cursor-not-allowed bg-slate-100 text-slate-400'
                          : 'btn-primary text-white shadow-sm'
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
                  <div className="mt-4 pl-5">
                    {/* Conclusion – promoted to top */}
                    {summaryConclusion && (
                      <div className="mb-3">
                        <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium ${conclusionBadge}`}>
                          <span className={`h-1.5 w-1.5 rounded-full ${conclusionDot}`} />
                          {summaryConclusion}
                        </span>
                      </div>
                    )}
                    {/* Summary text */}
                    <p className="text-[13px] leading-relaxed text-slate-600 text-justify">
                      {executiveSummary}
                    </p>
                    {/* Stat bar */}
                    <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
                      <span className="inline-flex items-center rounded-full bg-slate-100 px-2.5 py-1 font-medium text-slate-600">
                        All: {totalFieldsCount}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-1 font-medium text-amber-700">
                        Low confidence: {lowConfidenceFieldsCount}
                      </span>
                      <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700">
                        Reviewed: {reviewedFieldsCount}
                      </span>
                    </div>
                  </div>
                ) : (
                  <div className="mt-4 pl-5 text-[13px] text-slate-400">
                    No executive summary available.
                  </div>
                )}
              </details>
            </div>

            {/* Key Fields */}
            <div
              className="card relative z-20 px-6 py-5 animate-fade-in"
              style={{ opacity: 0, animationDelay: '60ms' }}
            >
              <details open>
                <summary className="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800">
                  <span className="ml-2 inline-flex items-center gap-1.5">
                    Key Fields
                    <span className="info-tip info-tip-down" data-tip="Important fields identified for quick review, such as policy number and incident details">i</span>
                    <span className="inline-flex items-center rounded-full bg-accent-subtle px-2 py-0.5 text-xs font-medium text-accent">{keyClaimFields.length}</span>
                  </span>
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

            {/* Low Confidence Fields */}
            <div
              className="card relative z-10 px-6 py-5 animate-fade-in"
              style={{ opacity: 0, animationDelay: '120ms' }}
            >
              <details>
                <summary className="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800">
                  <span className="ml-2 inline-flex items-center gap-1.5">
                    Low Confidence Fields
                    <span className="info-tip info-tip-down" data-tip="Fields with extraction confidence below 80%. Review and correct these fields before exporting">i</span>
                    <span className="inline-flex items-center rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-700">{lowConfidenceFields.length}</span>
                  </span>
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

            {/* All Fields */}
            <div
              className="card relative px-6 py-5 animate-fade-in"
              style={{ opacity: 0, animationDelay: '180ms' }}
            >
              <details>
                <summary className="cursor-pointer select-none pl-5 text-[15px] font-semibold text-slate-800">
                  <span className="ml-2 inline-flex items-center gap-1.5">
                    All Fields
                    <span className="info-tip info-tip-down" data-tip="Complete list of every field extracted from the document">i</span>
                    <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600">{claimFields.length}</span>
                  </span>
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
          /* ── Empty state ────────────────────────── */
          <div className={rightPanelClassName}>
            <div className="flex flex-1 flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-white p-8">
              <div className="flex flex-1 flex-col items-center justify-center gap-5">
                <div className="rounded-2xl bg-accent-subtle p-5">
                  <svg className="h-10 w-10 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                  </svg>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium text-slate-700">No form processed yet</p>
                  <p className="mt-1 text-[13px] text-slate-400">Choose a demo form or upload your own PDF, then click <span className="font-medium text-slate-600">&quot;Process Form&quot;</span>.</p>
                </div>
                {/* Connected step indicator */}
                <div className="mt-1 flex items-center text-[13px] text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-subtle text-[11px] font-semibold text-accent">1</span>
                    <span>Choose a demo form or upload your own</span>
                  </div>
                  <div className="mx-3 h-px w-6 bg-slate-200" />
                  <div className="flex items-center gap-1.5">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent-subtle text-[11px] font-semibold text-accent">2</span>
                    <span>Process</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
