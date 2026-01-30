export interface ClaimField {
  id: string;
  label: string;
  value: string;
  confidence: string;
}

interface ClaimTableProps {
  fields: ClaimField[];
  activeFieldId?: string | null;
  onHover?: (fieldId: string | null) => void;
  className?: string;
}

export default function ClaimTable({
  fields,
  activeFieldId,
  onHover,
  className,
}: ClaimTableProps) {
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
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {fields.map((field) => {
              const isActive = activeFieldId === field.id;
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
                  <td className="py-3 pr-4 text-slate-600">{field.value}</td>
                  <td className="py-3 text-right w-24">
                    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      parseFloat(field.confidence) >= 80
                        ? 'bg-emerald-50 text-emerald-700'
                        : parseFloat(field.confidence) >= 60
                          ? 'bg-amber-50 text-amber-700'
                          : 'bg-rose-50 text-rose-700'
                    }`}>
                      {field.confidence}
                    </span>
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
