import { useEffect, useRef, useState } from "react";

export function useTaskStream(sellerId, onTaskUpdate) {
  const wsRef = useRef(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    if (!sellerId) return;

    const url = `ws://localhost:8000/api/tasks/stream?seller_id=${sellerId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => setIsConnected(false);
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onTaskUpdate?.(data);
      } catch {
        // ignore parse errors
      }
    };

    return () => {
      ws.close();
    };
  }, [sellerId]);

  return { isConnected };
}
