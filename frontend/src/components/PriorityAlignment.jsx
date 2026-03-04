const ALIGNMENT_COLOR = {
  HIGH: "text-green-400 bg-green-900/30",
  MEDIUM: "text-yellow-400 bg-yellow-900/30",
  LOW: "text-gray-400 bg-gray-800",
};

export default function PriorityAlignment({ priorities = [], className = "" }) {
  if (!priorities.length) return null;

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg p-4 ${className}`}>
      <h2 className="text-sm font-semibold text-gray-300 mb-3">Priority Alignment</h2>
      <div className="space-y-2">
        {priorities.map((p, i) => (
          <div key={i} className="flex items-start gap-3">
            <span className={`text-xs font-bold px-1.5 py-0.5 rounded flex-shrink-0 mt-0.5 ${ALIGNMENT_COLOR[p.alignment] ?? ALIGNMENT_COLOR.LOW}`}>
              {p.alignment}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-200">{p.priority}</p>
              {p.platform_products?.length > 0 && (
                <p className="text-xs text-gray-500 mt-0.5">
                  Products: {p.platform_products.join(", ")}
                </p>
              )}
              {p.source && (
                <p className="text-xs text-gray-600 mt-0.5">Source: {p.source}</p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
