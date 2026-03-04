import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts";

const DIMENSIONS = ["product_knowledge", "contact_knowledge", "objection_handling", "conversation_flow", "confidence"];

export default function ScorecardView({ scorecard, score, className = "" }) {
  if (!scorecard && score == null) return null;

  const data = scorecard
    ? DIMENSIONS.map((dim) => ({
        dimension: dim.replace("_", " "),
        score: scorecard[dim] ?? 0,
      }))
    : null;

  return (
    <div className={`${className}`}>
      {data ? (
        <div>
          <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Readiness Scorecard</h3>
          <ResponsiveContainer width="100%" height={200}>
            <RadarChart data={data}>
              <PolarGrid stroke="#374151" />
              <PolarAngleAxis dataKey="dimension" tick={{ fill: "#9ca3af", fontSize: 10 }} />
              <Radar dataKey="score" stroke="#3b82f6" fill="#3b82f6" fillOpacity={0.3} />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="flex items-center gap-2">
          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${score >= 7 ? "bg-green-900/40 text-green-400" : "bg-yellow-900/40 text-yellow-400"}`}>
            {score}
          </div>
          <span className="text-xs text-gray-500">
            {score >= 7 ? "Ready to call" : "More practice recommended"}
          </span>
        </div>
      )}
    </div>
  );
}
