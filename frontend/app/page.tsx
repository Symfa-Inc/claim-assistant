'use client'


import { useEffect, useRef, useState } from 'react';
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
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const claimFields: ClaimField[] = [
    { id: 'policy_id', label: 'Policy ID', value: 'POL123456789', confidence: '95%' },
    { id: 'insured_name', label: 'Insured name', value: 'Emy Hunt', confidence: '97%' },
    { id: 'incident_date', label: 'Incident date', value: '2025-11-03', confidence: '93%' },
    { id: 'report_date', label: 'Report date', value: '2025-11-04', confidence: '92%' },
    { id: 'loss_type', label: 'Loss type', value: 'Water damage', confidence: '90%' },
    {
      id: 'loss_description',
      label: 'Loss description',
      value: 'Burst pipe in kitchen caused ceiling leak.',
      confidence: '88%',
    },
    {
      id: 'location_address',
      label: 'Location/address',
      value: '312 Cedar Ave, Springdale, CA',
      confidence: '91%',
    },
  ];

  const highlightBoxes: HighlightBox[] = [
    {
      id: 'box_policy',
      fieldId: 'policy_id',
      page: 1,
      vertices: [
        { x: 72, y: 120 },
        { x: 252, y: 120 },
        { x: 252, y: 144 },
        { x: 72, y: 144 },
      ],
    },
    {
      id: 'box_name',
      fieldId: 'insured_name',
      page: 1,
      vertices: [
        { x: 72, y: 165 },
        { x: 282, y: 165 },
        { x: 282, y: 189 },
        { x: 72, y: 189 },
      ],
    },
    {
      id: 'box_incident',
      fieldId: 'incident_date',
      page: 1,
      vertices: [
        { x: 72, y: 210 },
        { x: 212, y: 210 },
        { x: 212, y: 234 },
        { x: 72, y: 234 },
      ],
    },
    {
      id: 'box_report',
      fieldId: 'report_date',
      page: 1,
      vertices: [
        { x: 72, y: 255 },
        { x: 212, y: 255 },
        { x: 212, y: 279 },
        { x: 72, y: 279 },
      ],
    },
    {
      id: 'box_loss_type',
      fieldId: 'loss_type',
      page: 1,
      vertices: [
        { x: 72, y: 300 },
        { x: 232, y: 300 },
        { x: 232, y: 324 },
        { x: 72, y: 324 },
      ],
    },
    {
      id: 'box_loss_desc',
      fieldId: 'loss_description',
      page: 1,
      vertices: [
        { x: 72, y: 350 },
        { x: 412, y: 350 },
        { x: 412, y: 410 },
        { x: 72, y: 410 },
      ],
    },
    {
      id: 'box_location',
      fieldId: 'location_address',
      page: 1,
      vertices: [
        { x: 72, y: 430 },
        { x: 352, y: 430 },
        { x: 352, y: 458 },
        { x: 72, y: 458 },
      ],
    },
  ];

  useEffect(() => {
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);

  const handleProcess = () => {
    if (isProcessing) return;
    setShowTable(false);
    setIsProcessing(true);

    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    timerRef.current = setTimeout(() => {
      setIsProcessing(false);
      setShowTable(true);
    }, 1500);
  };

  return (
    <main className="flex h-screen flex-col">
      <header className="bg-blue-600 text-white">
        <div className="mx-auto px-4 py-4 text-2xl font-semibold">
          Claim Assistant
        </div>
      </header>
      <div className="ml-4 mr-4 flex flex-1 min-h-0 flex-col gap-4 py-4 md:flex-row">
        <div className="flex min-h-0 flex-1 items-stretch md:w-2/4 md:px-0">
          <div className="flex min-h-0 w-full flex-1 flex-col rounded-lg bg-gray-50 p-4">
            <AppPdfViewer
              isProcessing={isProcessing}
              onProcess={handleProcess}
              highlightFieldId={showTable ? hoveredFieldId : null}
              highlightBoxes={highlightBoxes}
            />
          </div>
        </div>
        {isProcessing ? (
          <div className="flex min-h-0 flex-1 flex-col rounded-lg bg-gray-50 p-4 md:w-2/4 md:px-10">
            <h2 className="text-lg font-semibold text-gray-800">
              Extracted Claim Fields
            </h2>
            <div className="mt-6 flex flex-1 flex-col items-center justify-center gap-3 text-gray-600">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-blue-600" />
              <span className="text-sm font-medium">Processing...</span>
            </div>
          </div>
        ) : showTable ? (
          <ClaimTable
            fields={claimFields}
            activeFieldId={hoveredFieldId}
            onHover={setHoveredFieldId}
          />
        ) : (
          <div className="flex min-h-0 flex-1 flex-col rounded-lg bg-gray-50 p-4 md:w-2/4 md:px-10">
            <h2 className="text-lg font-semibold text-gray-800">
              Extracted Claim Fields
            </h2>
            <div className="mt-6 flex flex-1 flex-col items-center justify-center text-sm text-gray-500">
              Upload a PDF and click “Process PDF” to view extracted fields.
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
