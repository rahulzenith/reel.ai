import { formatTime } from "../../lib/format";

interface Props {
  connected: boolean;
  runStatus: string;
  publishMode: string;
  nextScheduledRun: string | null;
  onRun: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  idle: "Idle",
  running: "Running pipeline...",
  completed: "Done — video ready",
  failed: "Run failed",
};

export default function Topbar({ connected, runStatus, publishMode, nextScheduledRun, onRun }: Props) {
  return (
    <div className="flex items-center justify-between mb-6">
      <div className="flex items-center gap-3">
        <span
          className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-gray-400"}`}
          title={connected ? "Connected" : "Disconnected"}
        />
        <h1 className="text-lg font-semibold text-gray-900">Shorts Factory</h1>
        <span className="text-sm text-gray-500">{STATUS_LABELS[runStatus] ?? runStatus}</span>
        {publishMode === "dry_run" && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">DRY RUN</span>
        )}
      </div>
      <div className="flex items-center gap-3">
        {nextScheduledRun && (
          <span className="text-xs text-gray-400">next auto-run: {formatTime(nextScheduledRun)}</span>
        )}
        <button
          onClick={onRun}
          disabled={runStatus === "running"}
          className="px-4 py-1.5 text-sm bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Run now
        </button>
      </div>
    </div>
  );
}
