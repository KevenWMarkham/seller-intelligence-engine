const THREAT_COLOR = {
  high: "text-red-400 bg-red-900/30",
  medium: "text-yellow-400 bg-yellow-900/30",
  low: "text-green-400 bg-green-900/30",
};

export default function CompetitiveLandscape({ data, className = "" }) {
  if (!data?.competitors?.length && !data?.strengths?.length) return null;

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg p-4 ${className}`}>
      <h2 className="text-sm font-semibold text-gray-300 mb-3">Competitive Landscape</h2>

      {data.market_position && (
        <p className="text-xs text-gray-500 mb-3">
          Market position: <span className="text-gray-300 font-medium">{data.market_position}</span>
        </p>
      )}

      {data.competitors?.length > 0 && (
        <div className="mb-3">
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Competitors</h3>
          <div className="space-y-2">
            {data.competitors.map((comp, i) => (
              <div key={i} className="flex items-start justify-between gap-2">
                <div>
                  <span className="text-sm font-medium text-white">{comp.name}</span>
                  <p className="text-xs text-gray-500 mt-0.5">{comp.your_win_theme}</p>
                </div>
                <span className={`text-xs px-1.5 py-0.5 rounded flex-shrink-0 ${THREAT_COLOR[comp.threat_level] ?? "text-gray-400 bg-gray-800"}`}>
                  {comp.threat_level}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.strengths?.length > 0 && (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Strengths</h3>
          <ul className="text-xs text-gray-400 space-y-0.5">
            {data.strengths.map((s, i) => <li key={i}>• {s}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}
