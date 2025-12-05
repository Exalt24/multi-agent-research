import { useEffect, useState, useRef } from "react";

interface ResearchResults {
  research_plan?: string;
  competitor_profiles: Record<string, { analysis: string; sources: string[] }>;
  comparative_analysis: { analysis_text: string };
  executive_summary: string;
  final_report: string;
  visualizations: Array<{
    title: string;
    type: string;
    description: string;
  }>;
  cost_tracking: Array<Record<string, any>>;  // List of per-agent cost info (parallel-safe)
}

interface AgentStatus {
  agent: string;
  status: string;
  progress: number;
  message: string;
  data: Record<string, unknown>;
  timestamp: number;
}

interface ApprovalRequest {
  approval_id: string;
  agent: string;
  question: string;
  context: Record<string, any>;
  options: string[];
}

interface WebSocketMessage {
  type: string;
  session_id?: string;
  agent?: string;
  status?: string;
  progress?: number;
  message?: string;
  data?: ResearchResults | Record<string, unknown>;
  timestamp?: number;
  error?: string;
  // HITL fields
  approval_id?: string;
  question?: string;
  context?: Record<string, any>;
  options?: string[];
}

export function useWebSocket(sessionId: string) {
  const [agentStatuses, setAgentStatuses] = useState<
    Record<string, AgentStatus>
  >({});
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [finalResults, setFinalResults] = useState<ResearchResults | null>(
    null
  );
  const [workflowComplete, setWorkflowComplete] = useState(false);
  const [pendingApproval, setPendingApproval] = useState<ApprovalRequest | null>(null);
  const [researchPlan, setResearchPlan] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const workflowCompleteRef = useRef(false);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!sessionId) {
      console.error("Cannot connect: sessionId is missing");
      return;
    }

    const connectWebSocket = () => {
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
            const agentName = message.agent;
            setAgentStatuses((prev) => ({
              ...prev,
              [agentName]: {
                agent: agentName,
                status: message.status || "unknown",
                progress: message.progress || 0,
                message: message.message || "",
                data: (message.data as Record<string, unknown>) || {},
                timestamp: message.timestamp || Date.now(),
              },
            }));

            // If Coordinator completed, extract research plan from data
            if (agentName === "Coordinator Agent" && message.status === "completed" && message.data) {
              const data = message.data as Record<string, any>;
              if (data.research_plan) {
                setResearchPlan(data.research_plan as string);
              }
            }
          } else if (message.type === "approval_request") {
            // Human-in-the-Loop approval request
            setPendingApproval({
              approval_id: message.approval_id || "",
              agent: message.agent || "",
              question: message.question || "",
              context: (message.context as Record<string, any>) || {},
              options: message.options || ["Approve", "Reject"],
            });
          } else if (message.type === "approval_received") {
            // Approval was processed, clear pending
            setPendingApproval(null);
          } else if (message.type === "workflow_complete") {
            setWorkflowComplete(true);
            workflowCompleteRef.current = true;
            const results = (message.data as ResearchResults) || null;
            setFinalResults(results);
            // Extract research plan from final results
            if (results?.research_plan) {
              setResearchPlan(results.research_plan);
            }
            setPendingApproval(null); // Clear any pending approvals
          } else if (message.type === "workflow_failed") {
            setError(message.error || "Workflow failed");
            setPendingApproval(null); // Clear any pending approvals
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
        console.log(
          "WebSocket disconnected. Code:",
          event.code,
          "Reason:",
          event.reason
        );
        setIsConnected(false);

        // Auto-reconnect after 2 seconds if workflow not complete
        if (!workflowCompleteRef.current) {
          reconnectTimeoutRef.current = setTimeout(() => {
            if (!workflowCompleteRef.current) {
              console.log("Attempting reconnect...");
              connectWebSocket();
            }
          }, 2000);
        }
      };

      wsRef.current = ws;
    };

    // Small delay to let backend initialize session
    const timer = setTimeout(() => {
      connectWebSocket();
    }, 500);

    return () => {
      clearTimeout(timer);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [sessionId]);

  return {
    agentStatuses,
    isConnected,
    error,
    finalResults,
    workflowComplete,
    pendingApproval,
    researchPlan,
  };
}

export type { ApprovalRequest };
