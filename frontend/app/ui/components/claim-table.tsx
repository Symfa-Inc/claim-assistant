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
    'flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:w-2/4 md:px-6';
  return (
    <div className={containerClassName}>

      <div className="mt-2 overflow-auto">
        <table className="w-full table-fixed text-left text-sm text-slate-700">
          <thead className="text-xs uppercase text-slate-500">
            <tr>
              <th className="py-2 pr-12 w-96 bg-slate-50 rounded-l-md">Field</th>
              <th className="py-2 pr-4 bg-slate-50">Value</th>
              <th className="py-2 text-right w-24 bg-slate-50 rounded-r-md">
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
                  className={
                    isActive
                      ? 'bg-blue-50'
                      : 'hover:bg-slate-50/80'
                  }
                  onMouseEnter={() => onHover?.(field.id)}
                  onMouseLeave={() => onHover?.(null)}
                >
                  <td className="py-3 pr-12 font-medium text-slate-800 w-96">
                    {field.label}
                  </td>
                  <td className="py-3 pr-4 text-slate-700">{field.value}</td>
                  <td className="py-3 text-right w-24 text-slate-600">
                    {field.confidence}
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
