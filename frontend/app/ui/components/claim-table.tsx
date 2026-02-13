'use client';

import { useState } from 'react';

export interface ClaimField {
  id: string;
  label: string;
  value: string;
  confidence: string;
  validated?: boolean;
}

interface ClaimTableProps {
  fields: ClaimField[];
  activeFieldId?: string | null;
  onHover?: (fieldId: string | null) => void;
  onFieldValueChange?: (fieldId: string, value: string) => void;
  onFieldApprove?: (fieldId: string) => void;
  emptyMessage?: string;
  className?: string;
}

export default function ClaimTable({
  fields,
  activeFieldId,
  onHover,
  onFieldValueChange,
  onFieldApprove,
  emptyMessage,
  className,
}: ClaimTableProps) {
  const [editingFieldId, setEditingFieldId] = useState<string | null>(null);
  const [draftValues, setDraftValues] = useState<Record<string, string>>({});

  const beginEdit = (field: ClaimField) => {
    setDraftValues((current) => ({
      ...current,
      [field.id]: current[field.id] ?? field.value,
    }));
    setEditingFieldId(field.id);
  };

  const updateDraft = (fieldId: string, value: string) => {
    setDraftValues((current) => ({ ...current, [fieldId]: value }));
    onFieldValueChange?.(fieldId, value);
  };

  const approveField = (field: ClaimField) => {
    if (editingFieldId === field.id) {
      onFieldValueChange?.(field.id, draftValues[field.id] ?? field.value);
      setEditingFieldId(null);
    }
    onFieldApprove?.(field.id);
  };

  const containerClassName =
    className ??
    'flex min-h-0 flex-1 flex-col rounded-2xl border border-slate-200/60 bg-white/80 backdrop-blur-sm p-4 shadow-sm md:w-2/4 md:px-6';

  return (
    <div className={containerClassName}>
      <div className="mt-2 overflow-auto">
        <table className="w-full table-fixed text-left text-sm text-slate-600">
          <thead className="text-xs font-medium uppercase tracking-wider text-slate-500">
            <tr>
              <th className="py-2.5 pr-4 w-64 bg-slate-50/80 first:rounded-l-lg">Field</th>
              <th className="py-2.5 pr-4 bg-slate-50/80">Value</th>
              <th className="py-2.5 text-right w-24 bg-slate-50/80 last:rounded-r-lg">
                Confidence
              </th>
              <th className="py-2.5 pl-3 text-right w-24 bg-slate-50/80">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {fields.length === 0 && (
              <tr>
                <td className="py-4 text-sm text-slate-400" colSpan={4}>
                  {emptyMessage ?? 'No fields available.'}
                </td>
              </tr>
            )}
            {fields.map((field) => {
              const isActive = activeFieldId === field.id;
              const isEditing = editingFieldId === field.id;
              const isValidated = field.validated === true;
              const confidenceValue = parseFloat(field.confidence);
              return (
                <tr
                  key={field.id}
                  className={`transition-colors ${
                    isActive
                      ? 'bg-indigo-50/70'
                      : 'hover:bg-slate-50/80'
                  }`}
                  onMouseEnter={() => onHover?.(field.id)}
                  onMouseLeave={() => onHover?.(null)}
                >
                  <td className="py-3 pr-4 font-medium text-slate-700 w-56">
                    {field.label}
                  </td>
                  <td className="py-3 pr-4 text-slate-600">
                    {isEditing ? (
                      <input
                        value={draftValues[field.id] ?? field.value}
                        onChange={(event) =>
                          updateDraft(field.id, event.target.value)
                        }
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') {
                            event.preventDefault();
                            approveField(field);
                          }
                          if (event.key === 'Escape') {
                            setEditingFieldId(null);
                          }
                        }}
                        className="w-full rounded-md border border-slate-300 bg-white px-2 py-1 text-sm text-slate-700 focus:border-indigo-300 focus:outline-none focus:ring-2 focus:ring-indigo-100"
                        aria-label={`Edit ${field.label}`}
                      />
                    ) : (
                      field.value
                    )}
                  </td>
                  <td className="py-3 text-right w-24">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      isValidated || confidenceValue >= 80
                        ? 'bg-emerald-50 text-emerald-700'
                        : confidenceValue >= 60
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-rose-50 text-rose-700'
                    }`}>
                      {isValidated ? (
                        <>
                          <svg className="mr-1 h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                          </svg>
                          100%
                        </>
                      ) : (
                        field.confidence
                      )}
                    </span>
                  </td>
                  <td className="py-3 pl-3 text-right">
                    <div className="inline-flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => beginEdit(field)}
                        className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50"
                        aria-label={`Edit ${field.label}`}
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M15.232 5.232l3.536 3.536M9 11l6.232-6.232a2.5 2.5 0 113.536 3.536L12.536 14.536a4 4 0 01-1.414.94L8 16l.524-3.122A4 4 0 019 11z" />
                        </svg>
                      </button>
                      <button
                        type="button"
                        onClick={() => approveField(field)}
                        className={`inline-flex h-7 w-7 items-center justify-center rounded-md border transition-colors ${
                          isValidated
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                            : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700'
                        }`}
                        aria-label={`Approve ${field.label}`}
                      >
                        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
