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
    'flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:w-2/4 md:px-6';

  return (
    <div className={containerClassName}>
      <div className="mt-2 overflow-auto">
        <table className="w-full table-fixed text-left text-[13px] text-slate-600">
          <thead>
            <tr className="border-b border-slate-100">
              <th className="pb-2.5 pr-4 text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-64">Field</th>
              <th className="pb-2.5 pr-4 text-[10px] font-semibold uppercase tracking-wider text-slate-400">Value</th>
              <th className="pb-2.5 text-right text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-28">
                Confidence
              </th>
              <th className="pb-2.5 pl-3 text-right text-[10px] font-semibold uppercase tracking-wider text-slate-400 w-20">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100/80">
            {fields.length === 0 && (
              <tr>
                <td className="py-4 text-[13px] text-slate-400" colSpan={4}>
                  {emptyMessage ?? 'No fields available.'}
                </td>
              </tr>
            )}
            {fields.map((field) => {
              const isActive = activeFieldId === field.id;
              const isEditing = editingFieldId === field.id;
              const isValidated = field.validated === true;
              const confidenceValue = parseFloat(field.confidence);
              const confidencePercent = Number.isNaN(confidenceValue) ? 0 : confidenceValue;

              const isHigh = isValidated || confidencePercent >= 80;
              const isMedium = !isHigh && confidencePercent >= 60;

              const barColor = isHigh
                ? 'bg-emerald-400'
                : isMedium
                  ? 'bg-amber-400'
                  : 'bg-rose-400';
              const textColor = isHigh
                ? 'text-emerald-600'
                : isMedium
                  ? 'text-amber-600'
                  : 'text-rose-500';

              return (
                <tr
                  key={field.id}
                  className={`transition-all ${
                    isActive
                      ? 'bg-accent-subtle'
                      : 'hover:bg-slate-50/60'
                  }`}
                  style={isActive ? { boxShadow: 'inset 3px 0 0 #0d9488' } : undefined}
                  onMouseEnter={() => onHover?.(field.id)}
                  onMouseLeave={() => onHover?.(null)}
                >
                  <td className="py-2.5 pr-4 font-medium text-slate-700 w-56">
                    {field.label}
                  </td>
                  <td className="py-2.5 pr-4 text-slate-600">
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
                        className="w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-[13px] text-slate-700 focus:border-accent-light focus:outline-none focus:ring-2 focus:ring-accent-subtle"
                        aria-label={`Edit ${field.label}`}
                      />
                    ) : (
                      !field.value || field.value.toLowerCase() === 'null'
                        ? <span className="text-slate-300">&mdash;</span>
                        : field.value
                    )}
                  </td>
                  <td className="py-2.5 text-right w-28">
                    <div className="inline-flex items-center gap-2">
                      <div className="h-[3px] w-10 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full transition-all ${barColor}`}
                          style={{ width: `${isValidated ? 100 : confidencePercent}%` }}
                        />
                      </div>
                      <span className={`text-xs font-medium tabular-nums ${textColor}`}>
                        {isValidated ? (
                          <span className="inline-flex items-center gap-0.5">
                            <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                            </svg>
                            100%
                          </span>
                        ) : (
                          field.confidence
                        )}
                      </span>
                    </div>
                  </td>
                  <td className="py-2.5 pl-3 text-right">
                    <div className="inline-flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => beginEdit(field)}
                        className="inline-flex h-7 w-7 items-center justify-center rounded-md border border-slate-200 bg-white text-slate-500 transition-colors hover:border-slate-300 hover:text-slate-700"
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
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-600'
                            : 'border-slate-200 bg-white text-slate-500 hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-600'
                        }`}
                        aria-label={`Approve ${field.label}`}
                      >
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
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
