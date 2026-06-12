import { formatTime } from "../../lib/format";

interface Props {
  connected: boolean;
  runStatus: string;
  publishMode: string;
  nextScheduledRun: string | null;
  topic: string;
  content: string;
  showContent: boolean;
  onTopicChange: (v: string) => void;
  onContentChange: (v: string) => void;
  onToggleContent: () => void;
  onRun: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  idle: "Idle — ready to create",
  running: "Pipeline running",
  completed: "Done — video ready",
  failed: "Run failed",
};

export default function Topbar({
  connected, runStatus, publishMode, nextScheduledRun,
  topic, content, showContent,
  onTopicChange, onContentChange, onToggleContent, onRun,
}: Props) {
  const running = runStatus === "running";
  return (
    <div className="sticky top-0 z-10 -mx-6 px-6 py-4 mb-6 backdrop-blur-xl bg-slate-950/70 border-b border-slate-800/60">
      <div className="max-w-6xl mx-auto">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 shrink-0">
            <span className="relative flex h-2.5 w-2.5">
              {connected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              )}
              <span
                className={`relative inline-flex rounded-full h-2.5 w-2.5 ${connected ? "bg-emerald-400" : "bg-slate-600"}`}
              />
            </span>
            <h1 className="text-lg font-semibold tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent whitespace-nowrap">
              Shorts Factory
            </h1>
            {publishMode === "dry_run" && (
              <span className="text-[11px] px-2 py-0.5 rounded-full bg-amber-400/10 text-amber-400 border border-amber-400/20 font-medium tracking-wide">
                DRY RUN
              </span>
            )}
          </div>

          <div className="flex items-center gap-2 flex-1 max-w-xl">
            <input
              type="text"
              value={topic}
              onChange={(e) => onTopicChange(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && !running && onRun()}
              disabled={running}
              placeholder="Optional: your own topic — empty = auto-discover trends"
              className="flex-1 px-3 py-2 text-sm rounded-xl bg-slate-900/80 border border-slate-700/60
                         text-slate-200 placeholder-slate-600 outline-none
                         focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30
                         disabled:opacity-40 transition-colors"
            />
            <button
              onClick={onToggleContent}
              disabled={running}
              className={`px-3 py-2 text-xs rounded-xl border transition-colors disabled:opacity-40 whitespace-nowrap ${
                showContent || content
                  ? "border-emerald-500/40 text-emerald-400 bg-emerald-500/10"
                  : "border-slate-700/60 text-slate-400 hover:text-slate-200"
              }`}
              title="Paste source material for the script"
            >
              + content{content ? " ✓" : ""}
            </button>
          </div>

          <div className="flex items-center gap-4 shrink-0">
            <div className="text-right hidden md:block">
              <p className={`text-xs ${running ? "text-emerald-400" : "text-slate-500"}`}>
                {STATUS_LABELS[runStatus] ?? runStatus}
              </p>
              {nextScheduledRun && (
                <p className="text-[10px] text-slate-600">auto-run {formatTime(nextScheduledRun)}</p>
              )}
            </div>
            <button
              onClick={onRun}
              disabled={running}
              className="px-5 py-2 text-sm font-medium rounded-xl text-white
                         bg-gradient-to-r from-emerald-500 to-teal-500
                         hover:from-emerald-400 hover:to-teal-400 hover:scale-[1.03]
                         active:scale-[0.98] transition-all duration-200
                         shadow-lg shadow-emerald-500/20
                         disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:scale-100"
            >
              {running ? "Running…" : "▶ Run now"}
            </button>
          </div>
        </div>

        {showContent && (
          <textarea
            value={content}
            onChange={(e) => onContentChange(e.target.value)}
            disabled={running}
            rows={4}
            maxLength={4000}
            placeholder="Paste source material — an article, your notes, product info… The script's facts will come from this instead of web search."
            className="mt-3 w-full px-3 py-2 text-sm rounded-xl bg-slate-900/80 border border-slate-700/60
                       text-slate-200 placeholder-slate-600 outline-none resize-y
                       focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/30
                       disabled:opacity-40 transition-colors animate-fade-up"
          />
        )}
      </div>
    </div>
  );
}
