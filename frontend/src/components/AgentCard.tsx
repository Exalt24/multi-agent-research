interface AgentCardProps {
  name: string;
  description: string;
  status: string;
  progress: number;
  message: string;
}

export default function AgentCard({
  name,
  description,
  status,
  progress,
  message,
}: AgentCardProps) {
  // "Not started yet" is a different thing from "started and at zero", and the UI
  // has to say which. Anything that is not a known active or finished state is
  // treated as queued, so an unrecognised status from the backend degrades to the
  // honest reading rather than claiming 0% progress.
  const isQueued = !["running", "completed", "failed"].includes(status);

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

  /**
   * Status pills carry a GLYPH as well as a colour.
   *
   * Every state was previously distinguished by hue alone, so Running and Pending
   * were the same pill in two colours and a colour-blind viewer could not tell a
   * working agent from an idle one. WCAG 1.4.1 is explicit that colour must not be
   * the only means of conveying information, and this is a run view where "is it
   * moving" is the entire question. The glyph is aria-hidden because the adjacent
   * word already says the state.
   */
  const getStatusBadge = () => {
    const base = "inline-flex items-center gap-1.5 px-2 py-1 text-xs rounded-full";
    switch (status) {
      case "completed":
        return (
          <span className={`${base} bg-green-500/20 text-green-300`}>
            <svg viewBox="0 0 16 16" className="h-3 w-3" fill="currentColor" aria-hidden="true">
              <path d="M6.2 11.3 3.4 8.5l1-1 1.8 1.8 4.4-4.4 1 1z" />
            </svg>
            Completed
          </span>
        );
      case "running":
        return (
          <span className={`${base} bg-blue-500/20 text-blue-300`}>
            <svg viewBox="0 0 16 16" className="h-3 w-3 animate-spin" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
              <path d="M8 2a6 6 0 1 1-4.2 1.8" strokeLinecap="round" />
            </svg>
            Running
          </span>
        );
      case "failed":
        return (
          <span className={`${base} bg-red-500/20 text-red-300`}>
            <svg viewBox="0 0 16 16" className="h-3 w-3" fill="currentColor" aria-hidden="true">
              <path d="M8 1.5A6.5 6.5 0 1 0 8 14.5 6.5 6.5 0 0 0 8 1.5m.9 9.6H7.1V9.9h1.8zm0-2.4H7.1V4.4h1.8z" />
            </svg>
            Failed
          </span>
        );
      default:
        return (
          <span className={`${base} bg-gray-500/20 text-gray-300`}>
            <svg viewBox="0 0 16 16" className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden="true">
              <circle cx="8" cy="8" r="5.5" />
              <path d="M8 5.2V8l2 1.4" strokeLinecap="round" />
            </svg>
            Queued
          </span>
        );
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

      {/* Progress.
          Two changes over the previous version, both from the reference pass.

          A queued agent used to read "Progress 0%" with an empty bar. Four of the
          seven sit there for most of a run, so the screen showed four agents that
          looked stuck at zero rather than four that had not been reached yet. It
          says "Waiting its turn" now and the numeric readout is reserved for
          agents that have actually started. GitHub Actions is the reference here:
          a job that has not begun shows a queued state, never 0%.

          And the bar is a real progressbar to assistive tech. It was a pair of
          divs, so a screen reader announced nothing at all; it now carries the
          role and the value, with aria-valuenow omitted while queued because the
          value is genuinely unknown rather than zero. */}
      <div className="mb-3">
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Progress</span>
          <span>{isQueued ? "Waiting its turn" : `${progress}%`}</span>
        </div>
        <div
          className="w-full bg-gray-700 rounded-full h-2 overflow-hidden"
          role="progressbar"
          aria-label={`${name} progress`}
          aria-valuemin={0}
          aria-valuemax={100}
          {...(isQueued ? {} : { "aria-valuenow": progress })}
        >
          <div
            className={`h-full transition-all duration-500 ${
              status === "completed"
                ? "bg-green-500"
                : status === "running"
                ? "bg-blue-500"
                : status === "failed"
                ? "bg-red-500"
                : "bg-gray-600"
            }`}
            style={{ width: `${isQueued ? 0 : progress}%` }}
          />
        </div>
      </div>

      {/* Status Message */}
      <div className="text-xs text-gray-400">{message}</div>
    </div>
  );
}
