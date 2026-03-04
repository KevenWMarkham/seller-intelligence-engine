import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getTask } from "../api/client";
import ContactCard from "./ContactCard";
import CoachingPanel from "./CoachingPanel";
import ISVRecommendations from "./ISVRecommendations";
import MotionBadge from "./MotionBadge";

export default function TaskDetail() {
  const { taskId } = useParams();
  const { data: task, isLoading, error } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => getTask(taskId),
  });

  if (isLoading) return <div className="p-6 text-gray-500 text-sm">Loading task...</div>;
  if (error) return <div className="p-6 text-red-400 text-sm">Error: {error.message}</div>;

  const brief = task?.conversation_brief_json ? JSON.parse(task.conversation_brief_json) : null;
  const isvs = task?.isv_recommendations_json ? JSON.parse(task.isv_recommendations_json) : [];

  return (
    <div className="max-w-4xl mx-auto px-6 py-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <a href="/" className="text-gray-500 hover:text-gray-300 text-sm">← Dashboard</a>
        <span className="text-gray-700">/</span>
        <span className="text-gray-300 text-sm">Task #{taskId}</span>
      </div>

      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-xl font-bold text-white">
            {task?.company?.name ?? `Company #${task?.company_id}`}
          </h1>
          <div className="flex items-center gap-2 mt-1">
            <MotionBadge motion={task?.sales_motion} />
            <span className="text-xs text-gray-500">{task?.platform_vendor}</span>
          </div>
        </div>
        <div className="text-3xl font-bold text-blue-400">{task?.priority_score ?? "—"}</div>
      </div>

      {/* Contact */}
      {task?.contact && <ContactCard contact={task.contact} className="mb-4" />}

      {/* Conversation Brief */}
      {brief && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 mb-4">
          <h2 className="text-sm font-semibold text-gray-300 mb-3">Conversation Brief</h2>
          <div className="space-y-3">
            <BriefSection label="Opener" content={brief.opener} />
            <BriefSection label="Why it matters" content={brief.why_it_matters} />
            <BriefSection label="Solution connection" content={brief.solution_connection} />
            <BriefSection label="Suggested ask" content={brief.suggested_ask} />
          </div>

          {brief.predicted_objections?.length > 0 && (
            <div className="mt-4">
              <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
                Predicted Objections
              </h3>
              <div className="space-y-2">
                {brief.predicted_objections.map((obj, i) => (
                  <div key={i} className="bg-gray-800/50 rounded p-3">
                    <p className="text-xs text-yellow-400 mb-1 font-medium">"{obj.objection}"</p>
                    <p className="text-xs text-gray-300">{obj.suggested_response}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ISV Recommendations */}
      <ISVRecommendations isvs={isvs} className="mb-4" />

      {/* Coaching Panel */}
      <CoachingPanel task={task} />
    </div>
  );
}

function BriefSection({ label, content }) {
  if (!content) return null;
  return (
    <div>
      <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{label}</span>
      <p className="text-sm text-gray-300 mt-1">{content}</p>
    </div>
  );
}
