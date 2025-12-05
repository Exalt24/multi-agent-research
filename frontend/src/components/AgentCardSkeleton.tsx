/**
 * Skeleton loader for AgentCard
 * Shows animated placeholders while agents are loading
 */
export default function AgentCardSkeleton() {
  return (
    <div className="rounded-lg p-5 border border-gray-700 bg-gray-800/30 animate-pulse">
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          {/* Agent name skeleton */}
          <div className="h-5 bg-gray-700 rounded w-3/4 mb-2"></div>
          {/* Description skeleton */}
          <div className="h-3 bg-gray-700 rounded w-full"></div>
        </div>
        {/* Status badge skeleton */}
        <div className="h-6 w-20 bg-gray-700 rounded-full ml-3"></div>
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <div className="h-3 bg-gray-700 rounded w-16"></div>
          <div className="h-3 bg-gray-700 rounded w-8"></div>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2"></div>
      </div>

      {/* Status Message skeleton */}
      <div className="h-3 bg-gray-700 rounded w-2/3"></div>
    </div>
  );
}
