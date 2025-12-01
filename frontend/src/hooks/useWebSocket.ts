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
  session_id?: string;
  agent?: string;
  status?: string;
  progress?: number;
  message?: string;
  data?: any;
  timestamp?: number;
  error?: string;
}

export function useWebSocket(sessionId: string) {
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finalResults, setFinalResults] = useState<any>(null);
  const [workflowComplete, setWorkflowComplete] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  const connect = useCallback(() => {
    if (!sessionId) {
      console.error("Cannot connect: sessionId is missing");
      return;
    }

    const wsUrl = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";
    const fullUrl = `${wsUrl}/ws/research/${sessionId}`;

    console.log("Connecting to WebSocket:", fullUrl);
    console.log("Session ID:", sessionId);

    const ws = new WebSocket(fullUrl);

    ws.onopen = () => {
      console.log("WebSocket connected");
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === "agent_status" && message.agent) {
          const agentName = message.agent as string; // Type assertion
          setAgentStatuses((prev) => ({
            ...prev,
            [agentName]: {
              agent: agentName,
              status: message.status || "unknown",
              progress: message.progress || 0,
              message: message.message || "",
              data: message.data || {},
              timestamp: message.timestamp || Date.now(),
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
      console.error("WebSocket URL was:", fullUrl);
      console.error("Session ID:", sessionId);
      // Don't set error state - let it reconnect automatically
    };

    ws.onclose = (event) => {
      console.log("WebSocket disconnected. Code:", event.code, "Reason:", event.reason);
      setIsConnected(false);

      // Auto-reconnect after 2 seconds (faster than before)
      setTimeout(() => {
        if (wsRef.current === ws && !workflowComplete) {
          console.log("Attempting reconnect...");
          connect();
        }
      }, 2000);
    };

    wsRef.current = ws;
  }, [sessionId, workflowComplete]);

  useEffect(() => {
    // Small delay to let backend initialize session
    const timer = setTimeout(() => {
      connect();
    }, 500);

    return () => {
      clearTimeout(timer);
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
