"use client";

import { useState } from "react";

type ApprovalContext = {
  report_preview?: string;
  concerns?: string;
  [key: string]: unknown;
};

interface ApprovalRequest {
  approval_id: string;
  agent: string;
  question: string;
  context: ApprovalContext;
  options: string[];
}

interface ApprovalModalProps {
  approval: ApprovalRequest;
  onRespond: (decision: string, feedback?: string) => void;
}

export default function ApprovalModal({
  approval,
  onRespond,
}: ApprovalModalProps) {
  const [feedback, setFeedback] = useState("");
  const [responding, setResponding] = useState(false);

  const handleDecision = async (decision: string) => {
    setResponding(true);
    await onRespond(decision, feedback || undefined);
    setResponding(false);
  };

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-linear-to-br from-gray-800 to-gray-900 rounded-xl p-8 max-w-2xl w-full border-2 border-yellow-500/50 shadow-2xl">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full animate-pulse"></div>
            <h2 className="text-2xl font-bold text-yellow-400">
              Human Approval Required
            </h2>
          </div>
          <p className="text-sm text-gray-400">
            Agent: <span className="text-white font-semibold">{approval.agent}</span>
          </p>
        </div>

        {/* Question */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-white mb-3">
            {approval.question}
          </h3>

          {/* Context */}
          {approval.context && Object.keys(approval.context).length > 0 && (
            <div className="bg-gray-900/50 rounded-lg p-4 mb-4 border border-gray-700">
              <h4 className="text-sm font-semibold text-gray-400 mb-2">
                Context:
              </h4>
              {approval.context.concerns && (
                <p className="text-sm text-yellow-300 mb-2">
                  {approval.context.concerns}
                </p>
              )}
              {approval.context.report_preview && (
                <div className="bg-gray-800 rounded p-3 text-xs text-gray-300 font-mono max-h-40 overflow-y-auto">
                  {approval.context.report_preview}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Feedback (Optional) */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-400 mb-2">
            Feedback (Optional)
          </label>
          <textarea
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
            placeholder="Add any comments or instructions..."
            className="w-full bg-gray-900/50 border border-gray-700 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
            rows={3}
          />
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3">
          {approval.options.map((option) => {
            const isStop = option.toLowerCase().includes("stop") || option.toLowerCase().includes("reject");
            const isContinue = option.toLowerCase().includes("continue") || option.toLowerCase().includes("approve");

            return (
              <button
                key={option}
                onClick={() => handleDecision(option)}
                disabled={responding}
                className={`flex-1 px-6 py-3 rounded-lg font-semibold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${
                  isStop
                    ? "bg-linear-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white"
                    : isContinue
                    ? "bg-linear-to-r from-green-600 to-green-700 hover:from-green-700 hover:to-green-800 text-white"
                    : "bg-linear-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white"
                }`}
              >
                {responding ? "Submitting..." : option}
              </button>
            );
          })}
        </div>

        {/* Info */}
        <p className="text-xs text-gray-500 mt-4 text-center">
          The workflow is paused. Your decision will determine how the research
          proceeds.
        </p>
      </div>
    </div>
  );
}
