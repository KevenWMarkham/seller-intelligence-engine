import { useState } from "react";
import { useTasks } from "../hooks/useTasks";
import PlatformSelector from "./PlatformSelector";
import TaskCard from "./TaskCard";

export default function Dashboard() {
  const sellerId = "seller-1"; // TODO: pull from auth context
  const [statusFilter, setStatusFilter] = useState(null);
  const [minPriority, setMinPriority] = useState(0);

  const { tasks, isLoading, error } = useTasks(sellerId, { status: statusFilter, min_priority: minPriority });

  return (
    <div className="flex flex-col min-h-screen bg-gray-950">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold text-white tracking-tight">NEXUS</span>
          <span className="text-xs text-gray-500 uppercase tracking-widest">Seller Intelligence</span>
        </div>
        <PlatformSelector />
      </header>

      <main className="flex-1 px-6 py-6 max-w-6xl mx-auto w-full">
        {/* Filters */}
        <div className="flex items-center gap-4 mb-6">
          <h1 className="text-lg font-semibold text-white">My Tasks</h1>
          <div className="flex gap-2 ml-auto">
            {["all", "ready", "in_progress", "created"].map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s === "all" ? null : s)}
                className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
                  (statusFilter === null && s === "all") || statusFilter === s
                    ? "bg-blue-600 text-white"
                    : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                }`}
              >
                {s.replace("_", " ")}
              </button>
            ))}
          </div>
          <select
            className="bg-gray-800 text-gray-300 text-xs rounded px-2 py-1 border border-gray-700"
            value={minPriority}
            onChange={(e) => setMinPriority(Number(e.target.value))}
          >
            <option value={0}>All priorities</option>
            <option value={80}>High (80+)</option>
            <option value={50}>Medium (50+)</option>
          </select>
        </div>

        {/* Task feed */}
        {isLoading && <div className="text-gray-500 text-sm">Loading tasks...</div>}
        {error && <div className="text-red-400 text-sm">Error: {error.message}</div>}
        {!isLoading && tasks?.length === 0 && (
          <div className="text-gray-500 text-sm">No tasks found.</div>
        )}
        <div className="flex flex-col gap-3">
          {tasks?.map((task) => (
            <TaskCard key={task.id} task={task} />
          ))}
        </div>
      </main>
    </div>
  );
}
