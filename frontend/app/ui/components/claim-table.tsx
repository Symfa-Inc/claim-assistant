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
}

export default function ClaimTable({
  fields,
  activeFieldId,
  onHover,
}: ClaimTableProps) {
  return (
    <div className="flex min-h-0 flex-1 flex-col rounded-lg bg-gray-50 p-4 md:w-2/4 md:px-10">
      <h2 className="text-lg font-semibold text-gray-800">
        Extracted Claim Fields
      </h2>
      <div className="mt-4 overflow-auto">
        <table className="w-full text-left text-sm text-gray-700">
          <thead className="text-xs uppercase text-gray-500">
            <tr>
              <th className="py-2 pr-4">Field</th>
              <th className="py-2 pr-4">Value</th>
              <th className="py-2 text-right">Confidence</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {fields.map((field) => {
              const isActive = activeFieldId === field.id;
              return (
                <tr
                  key={field.id}
                  className={isActive ? 'bg-blue-50' : undefined}
                  onMouseEnter={() => onHover?.(field.id)}
                  onMouseLeave={() => onHover?.(null)}
                >
                  <td className="py-3 pr-4 font-medium text-gray-800">
                    {field.label}
                  </td>
                  <td className="py-3 pr-4">{field.value}</td>
                  <td className="py-3 text-right">{field.confidence}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
