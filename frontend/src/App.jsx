import { Route, Routes } from "react-router-dom";
import Dashboard from "./components/Dashboard";
import TaskDetail from "./components/TaskDetail";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-950">
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/tasks/:taskId" element={<TaskDetail />} />
      </Routes>
    </div>
  );
}
