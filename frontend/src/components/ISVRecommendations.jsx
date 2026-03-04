export default function ISVRecommendations({ isvs = [], className = "" }) {
  if (!isvs.length) return null;

  return (
    <div className={`bg-gray-900 border border-gray-800 rounded-lg p-4 ${className}`}>
      <h2 className="text-sm font-semibold text-gray-300 mb-3">ISV Recommendations</h2>
      <div className="space-y-3">
        {isvs.map((isv, i) => (
          <div key={i} className="border border-gray-800 rounded p-3">
            <div className="flex items-center justify-between mb-1">
              <span className="font-semibold text-white text-sm">{isv.isv_name}</span>
              {isv.fit_score != null && (
                <span className="text-xs text-blue-400 font-medium">
                  Fit: {Math.round(isv.fit_score * 100)}%
                </span>
              )}
            </div>
            <p className="text-gray-400 text-xs">{isv.conversation_hook}</p>
            {isv.motion_alignment && (
              <span className="text-xs text-gray-500 mt-1 block">Motion: {isv.motion_alignment}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
