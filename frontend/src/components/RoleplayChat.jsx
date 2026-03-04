import { useState, useRef, useEffect } from "react";

export default function RoleplayChat({ session, task, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: "coach",
      content: `Ready to practice your call with ${task?.contact?.name ?? "the prospect"} at ${task?.company?.name ?? "the company"}. Go ahead — make your opening move.`,
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return;
    const userMsg = { role: "seller", content: input.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    // TODO: Phase 10 — call WebSocket or REST endpoint to get prospect response
    setTimeout(() => {
      setMessages((prev) => [
        ...prev,
        { role: "prospect", content: "Roleplay AI response coming in Phase 10." },
      ]);
      setIsLoading(false);
    }, 800);
  };

  return (
    <div className="mt-2">
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-gray-500 uppercase tracking-wide">Roleplay</span>
        <button onClick={onClose} className="text-xs text-gray-500 hover:text-gray-300">Close ✕</button>
      </div>

      {/* Message thread */}
      <div className="bg-gray-950 rounded-lg p-3 h-48 overflow-y-auto space-y-2 mb-2">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "seller" ? "justify-end" : "justify-start"}`}>
            <div className={`max-w-xs rounded-lg px-3 py-2 text-xs ${
              msg.role === "seller"
                ? "bg-blue-700 text-white"
                : msg.role === "coach"
                ? "bg-purple-900/50 text-purple-300 border border-purple-800"
                : "bg-gray-800 text-gray-200"
            }`}>
              {msg.role !== "seller" && (
                <span className="block text-xs font-semibold mb-0.5 opacity-60 uppercase">
                  {msg.role === "coach" ? "Coach" : task?.contact?.name ?? "Prospect"}
                </span>
              )}
              {msg.content}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 text-gray-400 rounded-lg px-3 py-2 text-xs">...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
          placeholder="Your message..."
          className="flex-1 bg-gray-800 border border-gray-700 text-gray-200 text-xs rounded px-3 py-2 focus:outline-none focus:border-blue-500"
        />
        <button
          onClick={sendMessage}
          disabled={isLoading}
          className="px-3 py-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-xs rounded font-medium"
        >
          Send
        </button>
      </div>
    </div>
  );
}
