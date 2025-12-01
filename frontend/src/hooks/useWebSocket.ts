import { useEffect, useState, useRef, useCallback } from "react";

interface AgentStatus {
  agent: string;
  status: string;
  progress: number;
  message: string;
  data: any;
  timestamp: number;
}

interface WebSocketMessage {
  type: string;
  session_id: string;
  agent: string;
  status: string;
  progress: number;
  message: string;
  data: any;
  timestamp: number;
}

export function useWebSocket(sessionId: string) {
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finalResults, setFinalResults] = useState<any>(null);
  const [workflowComplete, setWorkflowComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const ws = new WebSocket(`${wsUrl}/ws/research/${sessionId}`);

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === "agent_status") {
          setAgentStatuses((prev) => ({
            ...prev,
            [message.agent]: {
              agent: message.agent,
              status: message.status,
              progress: message.progress,
              message: message.message,
              data: message.data,
              timestamp: message.timestamp,
            },
          }));
        } else if (message.type === "workflow_complete") {
          setWorkflowComplete(true);
          setFinalResults(message.data);
        } else if (message.type === "workflow_failed") {
          setError(message.error || "Workflow failed");
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = (event) => {
      console.error("WebSocket error:", event);
      setError("WebSocket connection error");
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setIsConnected(false);

      // Attempt reconnect after 3 seconds
      setTimeout(() => {
        if (wsRef.current === ws) {
          console.log("Attempting reconnect...");
          connect();
        }
      }, 3000);
    };

    wsRef.current = ws;
  }, [sessionId]);

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [connect]);

  return {
    agentStatuses,
    isConnected,
    error,
    finalResults,
    workflowComplete,
  };
}
