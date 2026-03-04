import { useQuery } from "@tanstack/react-query";
import { getCompanySnapshot, getCompanyISVs } from "../api/client";
import CompetitiveLandscape from "./CompetitiveLandscape";
import PriorityAlignment from "./PriorityAlignment";
import ISVRecommendations from "./ISVRecommendations";

export default function SnapshotViewer({ companyId }) {
  const { data: snapshot, isLoading } = useQuery({
    queryKey: ["snapshot", companyId],
    queryFn: () => getCompanySnapshot(companyId),
    enabled: !!companyId,
  });

  const { data: isvData } = useQuery({
    queryKey: ["company-isvs", companyId],
    queryFn: () => getCompanyISVs(companyId),
    enabled: !!companyId,
  });

  if (isLoading) return <div className="text-gray-500 text-sm p-4">Loading snapshot...</div>;
  if (!snapshot) return null;

  const priorities = snapshot.priorities_json ? JSON.parse(snapshot.priorities_json) : [];
  const competitive = snapshot.competitive_json ? JSON.parse(snapshot.competitive_json) : null;
  const techStack = snapshot.tech_stack_json ? JSON.parse(snapshot.tech_stack_json) : [];

  return (
    <div className="space-y-4">
      {/* Company overview */}
      <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
        <h2 className="font-bold text-white text-base mb-1">{snapshot.name}</h2>
        <div className="flex gap-3 text-xs text-gray-500 mb-2 flex-wrap">
          {snapshot.industry && <span>{snapshot.industry}</span>}
          {snapshot.headcount && <span>{snapshot.headcount.toLocaleString()} employees</span>}
          {snapshot.revenue && <span>{snapshot.revenue} revenue</span>}
          {snapshot.stage && <span>{snapshot.stage}</span>}
          {snapshot.hq_location && <span>{snapshot.hq_location}</span>}
        </div>
        {snapshot.description && (
          <p className="text-gray-400 text-sm">{snapshot.description}</p>
        )}
      </div>

      {/* Tech stack */}
      {techStack.length > 0 && (
        <div className="bg-gray-900 border border-gray-800 rounded-lg p-4">
          <h3 className="text-sm font-semibold text-gray-300 mb-2">Tech Stack</h3>
          <div className="flex flex-wrap gap-2">
            {techStack.map((t, i) => (
              <span key={i} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded">
                {t.name ?? t}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Priority alignment */}
      {priorities.length > 0 && (
        <PriorityAlignment priorities={priorities} />
      )}

      {/* Competitive landscape */}
      {competitive && <CompetitiveLandscape data={competitive} />}

      {/* ISV ecosystem */}
      <ISVRecommendations isvs={isvData?.isvs ?? []} />
    </div>
  );
}
