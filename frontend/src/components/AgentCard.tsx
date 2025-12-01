interface AgentCardProps {
  name: string;
  description: string;
  status: string;
  progress: number;
  message: string;
}

export default function AgentCard({ name, description, status, progress, message }: AgentCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case "completed":
        return "border-green-500/50 bg-green-900/10";
      case "running":
        return "border-blue-500/50 bg-blue-900/10";
      case "failed":
        return "border-red-500/50 bg-red-900/10";
      default:
        return "border-gray-700 bg-gray-800/30";
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case "completed":
        return <span className="px-2 py-1 bg-green-500/20 text-green-400 text-xs rounded-full">Completed</span>;
      case "running":
        return <span className="px-2 py-1 bg-blue-500/20 text-blue-400 text-xs rounded-full animate-pulse">Running</span>;
      case "failed":
        return <span className="px-2 py-1 bg-red-500/20 text-red-400 text-xs rounded-full">Failed</span>;
      default:
        return <span className="px-2 py-1 bg-gray-500/20 text-gray-400 text-xs rounded-full">Pending</span>;
    }
  };

  return (
    <div className={`rounded-lg p-5 border transition-all ${getStatusColor()}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-white mb-1">{name}</h3>
          <p className="text-xs text-gray-400">{description}</p>
        </div>
        {getStatusBadge()}
      </div>

      {/* Progress Bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{progress}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
          <div
            className={`h-full transition-all duration-500 ${
              status === "completed" ? "bg-green-500" :
              status === "running" ? "bg-blue-500" :
              status === "failed" ? "bg-red-500" :
              "bg-gray-600"
            }`}
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="text-xs text-gray-400">
        {message}
      </div>
    </div>
  );
}
