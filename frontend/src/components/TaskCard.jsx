import { useNavigate } from "react-router-dom";
import MotionBadge from "./MotionBadge";

const PRIORITY_COLOR = (score) => {
  if (score >= 80) return "text-red-400 bg-red-900/30";
  if (score >= 50) return "text-yellow-400 bg-yellow-900/30";
  return "text-gray-400 bg-gray-800";
};

const STATUS_COLOR = {
  created: "text-gray-400",
  prepped: "text-blue-400",
  coached: "text-purple-400",
  ready: "text-green-400",
  in_progress: "text-yellow-400",
  completed: "text-gray-500",
  snoozed: "text-gray-500",
};

export default function TaskCard({ task }) {
  const navigate = useNavigate();
  const brief = task.conversation_brief_json ? JSON.parse(task.conversation_brief_json) : null;

  return (
    <div
      onClick={() => navigate(`/tasks/${task.id}`)}
      className="bg-gray-900 border border-gray-800 rounded-lg p-4 hover:border-gray-600 cursor-pointer transition-colors"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Company + contact */}
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-white text-sm">{task.company?.name ?? `Company #${task.company_id}`}</span>
            <span className="text-gray-500 text-xs">·</span>
            <span className="text-gray-400 text-xs truncate">{task.contact?.name ?? "—"}</span>
            {task.contact?.title && (
              <span className="text-gray-500 text-xs truncate">({task.contact.title})</span>
            )}
          </div>

          {/* Brief opener */}
          {brief?.opener && (
            <p className="text-gray-400 text-xs line-clamp-2 mb-2">{brief.opener}</p>
          )}

          {/* Badges */}
          <div className="flex items-center gap-2 flex-wrap">
            <MotionBadge motion={task.sales_motion} />
            <span className="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-400">
              {task.platform_vendor}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_COLOR[task.status] ?? "text-gray-400"}`}>
              {task.status?.replace("_", " ")}
            </span>
          </div>
        </div>

        {/* Priority score */}
        <div className={`text-lg font-bold px-3 py-1 rounded ${PRIORITY_COLOR(task.priority_score)}`}>
          {task.priority_score ?? "—"}
        </div>
      </div>
    </div>
  );
}
