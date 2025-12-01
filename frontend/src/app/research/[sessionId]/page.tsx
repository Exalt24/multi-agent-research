"use client";

import { use } from "react";
import { useWebSocket } from "@/hooks/useWebSocket";
import AgentCard from "@/components/AgentCard";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeSanitize from "rehype-sanitize";

interface PageProps {
  params: Promise<{ sessionId: string }>;
}

const AGENTS = [
  { name: "Coordinator Agent", description: "Plans research workflow" },
  { name: "Web Research Agent", description: "Gathers competitive intelligence" },
  { name: "Financial Intelligence Agent", description: "Researches funding and growth" },
  { name: "Data Analyst Agent", description: "Creates SWOT and comparisons" },
  { name: "Fact Checker Agent", description: "Validates claims" },
  { name: "Content Synthesizer Agent", description: "Writes final report" },
  { name: "Data Visualization Agent", description: "Generates chart specs" },
];

export default function ResearchPage({ params }: PageProps) {
  const { sessionId } = use(params);
  const { agentStatuses, isConnected, error, finalResults, workflowComplete } = useWebSocket(sessionId);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-gray-900 text-white">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">
            Research in Progress
          </h1>
          <p className="text-gray-400">
            Session ID: <code className="text-sm bg-gray-800 px-2 py-1 rounded">{sessionId}</code>
          </p>

          {/* Connection Status */}
          <div className="mt-4 flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? "Connected" : "Disconnected"}
            </span>
          </div>

          {error && (
            <div className="mt-4 p-3 bg-red-900/50 border border-red-700 rounded-lg text-red-200 text-sm">
              {error}
            </div>
          )}
        </div>

        {/* Agent Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {AGENTS.map((agent) => {
            const status = agentStatuses[agent.name];
            return (
              <AgentCard
                key={agent.name}
                name={agent.name}
                description={agent.description}
                status={status?.status || "pending"}
                progress={status?.progress || 0}
                message={status?.message || "Waiting to start..."}
              />
            );
          })}
        </div>

        {/* Overall Progress */}
        <div className="mt-8 bg-gray-800/50 backdrop-blur-sm rounded-xl p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Overall Progress</h2>
          <div className="space-y-2">
            {Object.entries(agentStatuses).map(([agent, status]) => (
              <div key={agent} className="flex items-center gap-3">
                <div className={`w-3 h-3 rounded-full ${
                  status.status === "completed" ? "bg-green-500" :
                  status.status === "running" ? "bg-blue-500 animate-pulse" :
                  status.status === "failed" ? "bg-red-500" :
                  "bg-gray-500"
                }`} />
                <div className="flex-1">
                  <div className="text-sm font-medium">{agent}</div>
                  <div className="text-xs text-gray-400">{status.message}</div>
                </div>
                <div className="text-sm text-gray-400">{status.progress}%</div>
              </div>
            ))}
          </div>
        </div>

        {/* Final Results */}
        {workflowComplete && finalResults && (
          <div className="mt-8 bg-gradient-to-br from-green-900/30 to-blue-900/30 backdrop-blur-sm rounded-xl p-8 border border-green-700/50">
            <h2 className="text-2xl font-bold mb-6 text-green-400">Research Complete!</h2>

            {/* Executive Summary */}
            {finalResults.executive_summary && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Executive Summary</h3>
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw, rehypeSanitize]}
                    components={{
                      h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-2 mt-4 text-purple-400" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-base font-semibold mb-2 mt-3 text-purple-300" {...props} />,
                      p: ({ node, ...props }) => <p className="mb-3 text-gray-300 leading-relaxed" {...props} />,
                      ul: ({ node, ...props }) => <ul className="mb-3 ml-5 space-y-1 list-disc" {...props} />,
                      ol: ({ node, ...props }) => <ol className="mb-3 ml-5 space-y-1 list-decimal" {...props} />,
                      li: ({ node, ...props }) => <li className="text-gray-300" {...props} />,
                      strong: ({ node, ...props }) => <strong className="text-white font-semibold" {...props} />,
                    }}
                  >
                    {finalResults.executive_summary}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Full Report */}
            {finalResults.final_report && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-2">Full Report</h3>
                <div className="prose prose-invert prose-lg max-w-none bg-gray-900/50 p-8 rounded-lg">
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    rehypePlugins={[rehypeRaw, rehypeSanitize]}
                    components={{
                      // Custom styling for better readability
                      h1: ({ node, ...props }) => <h1 className="text-3xl font-bold mb-6 mt-8 text-blue-300 border-b border-blue-800 pb-2" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-2xl font-bold mb-4 mt-6 text-blue-400" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-xl font-semibold mb-3 mt-5 text-purple-400" {...props} />,
                      h4: ({ node, ...props }) => <h4 className="text-lg font-semibold mb-2 mt-4 text-purple-300" {...props} />,
                      p: ({ node, ...props }) => <p className="mb-4 leading-relaxed text-gray-200" {...props} />,
                      ul: ({ node, ...props }) => <ul className="mb-4 ml-6 space-y-2 list-disc list-outside" {...props} />,
                      ol: ({ node, ...props }) => <ol className="mb-4 ml-6 space-y-2 list-decimal list-outside" {...props} />,
                      li: ({ node, ...props }) => <li className="text-gray-200 leading-relaxed" {...props} />,
                      table: ({ node, ...props }) => (
                        <div className="overflow-x-auto my-6">
                          <table className="min-w-full divide-y divide-gray-700 border border-gray-700" {...props} />
                        </div>
                      ),
                      thead: ({ node, ...props }) => <thead className="bg-gray-800" {...props} />,
                      th: ({ node, ...props }) => <th className="px-4 py-3 text-left text-sm font-semibold text-blue-300" {...props} />,
                      td: ({ node, ...props }) => <td className="px-4 py-3 text-sm text-gray-200 border-t border-gray-700" {...props} />,
                      blockquote: ({ node, ...props }) => (
                        <blockquote className="border-l-4 border-blue-500 pl-4 my-4 italic text-gray-300 bg-gray-800/50 py-2" {...props} />
                      ),
                      code: ({ node, inline, ...props }: any) =>
                        inline ? (
                          <code className="bg-gray-800 text-blue-300 px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                        ) : (
                          <code className="block bg-gray-800 text-green-300 p-4 rounded-lg overflow-x-auto text-sm font-mono my-4" {...props} />
                        ),
                      pre: ({ node, ...props }) => <pre className="bg-gray-800 rounded-lg overflow-x-auto my-4" {...props} />,
                      a: ({ node, ...props }) => <a className="text-blue-400 hover:text-blue-300 underline" target="_blank" rel="noopener noreferrer" {...props} />,
                      hr: ({ node, ...props }) => <hr className="my-6 border-gray-700" {...props} />,
                      strong: ({ node, ...props }) => <strong className="font-bold text-white" {...props} />,
                      em: ({ node, ...props }) => <em className="italic text-gray-300" {...props} />,
                    }}
                  >
                    {finalResults.final_report}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Competitor Profiles */}
            {finalResults.competitor_profiles && Object.keys(finalResults.competitor_profiles).length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold mb-4">Competitor Profiles</h3>
                <div className="space-y-4">
                  {Object.entries(finalResults.competitor_profiles).map(([company, profile]: [string, any]) => (
                    <div key={company} className="bg-gray-900/50 rounded-lg p-6 border border-gray-700">
                      <h4 className="text-xl font-bold text-blue-400 mb-4 border-b border-blue-900 pb-2">{company}</h4>
                      <div className="prose prose-invert max-w-none">
                        <ReactMarkdown
                          remarkPlugins={[remarkGfm]}
                          rehypePlugins={[rehypeRaw, rehypeSanitize]}
                          components={{
                            h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-2 mt-4 text-purple-400" {...props} />,
                            h3: ({ node, ...props }) => <h3 className="text-base font-semibold mb-2 mt-3 text-purple-300" {...props} />,
                            p: ({ node, ...props }) => <p className="mb-3 text-gray-300 leading-relaxed" {...props} />,
                            ul: ({ node, ...props }) => <ul className="mb-3 ml-5 space-y-1 list-disc" {...props} />,
                            li: ({ node, ...props }) => <li className="text-gray-300" {...props} />,
                            strong: ({ node, ...props }) => <strong className="text-white font-semibold" {...props} />,
                          }}
                        >
                          {profile.analysis}
                        </ReactMarkdown>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Download Buttons */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  // Create markdown content
                  let markdownContent = "# Market Research Report\n\n";

                  if (finalResults.executive_summary) {
                    markdownContent += "## Executive Summary\n\n";
                    markdownContent += finalResults.executive_summary + "\n\n";
                  }

                  if (finalResults.final_report) {
                    markdownContent += finalResults.final_report + "\n\n";
                  }

                  if (finalResults.comparative_analysis?.analysis_text) {
                    markdownContent += "## Comparative Analysis\n\n";
                    markdownContent += finalResults.comparative_analysis.analysis_text + "\n\n";
                  }

                  // Download as markdown
                  const blob = new Blob([markdownContent], { type: 'text/markdown' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `research-report-${sessionId.slice(0, 8)}.md`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-6 py-3 rounded-lg font-semibold"
              >
                Download Report (.md)
              </button>

              <button
                onClick={() => {
                  const blob = new Blob([JSON.stringify(finalResults, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `research-data-${sessionId.slice(0, 8)}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="bg-gray-700 hover:bg-gray-600 text-white px-6 py-3 rounded-lg font-semibold"
              >
                Download Data (.json)
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
