import { useState } from "react";
import { startRoleplay } from "../api/client";
import ScorecardView from "./ScorecardView";
import RoleplayChat from "./RoleplayChat";

export default function CoachingPanel({ task }) {
  const [mode, setMode] = useState(null); // null | "prep" | "roleplay" | "debrief"
  const [session, setSession] = useState(null);

  const handleStartRoleplay = async () => {
    try {
      const result = await startRoleplay("seller-1", task?.id);
      setSession(result);
      setMode("roleplay");
    } catch (err) {
      console.error(err);
    }
  };

  const coachingStatus = task?.coaching_status ?? "not_started";
  const readinessScore = task?.readiness_score;

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-gray-300">AI Sales Coach</h2>
        <div className="flex items-center gap-2">
          {readinessScore != null && (
            <span className={`text-xs font-bold px-2 py-0.5 rounded ${readinessScore >= 7 ? "bg-green-900/40 text-green-400" : "bg-yellow-900/40 text-yellow-400"}`}>
              Readiness: {readinessScore}/10
            </span>
          )}
          <span className="text-xs text-gray-500 capitalize">{coachingStatus.replace("_", " ")}</span>
        </div>
      </div>

      {mode === null && (
        <div className="flex gap-2 flex-wrap">
          <button
            onClick={() => setMode("prep")}
            className="px-3 py-1.5 bg-blue-700 hover:bg-blue-600 text-white text-xs rounded font-medium transition-colors"
          >
            Prep for Call
          </button>
          <button
            onClick={handleStartRoleplay}
            className="px-3 py-1.5 bg-purple-700 hover:bg-purple-600 text-white text-xs rounded font-medium transition-colors"
          >
            Practice Roleplay
          </button>
          <button
            onClick={() => setMode("debrief")}
            className="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 text-white text-xs rounded font-medium transition-colors"
          >
            Post-Call Debrief
          </button>
        </div>
      )}

      {mode === "roleplay" && session && (
        <RoleplayChat session={session} task={task} onClose={() => setMode(null)} />
      )}

      {mode === "prep" && (
        <div className="text-sm text-gray-400 mt-2">
          Pre-call prep package generation coming in Phase 10.
          <button onClick={() => setMode(null)} className="ml-2 text-blue-400 hover:underline">← Back</button>
        </div>
      )}

      {readinessScore != null && <ScorecardView score={readinessScore} className="mt-3" />}
    </div>
  );
}
