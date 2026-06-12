import { formatScore, formatTime } from "../../lib/format";
import type { RunHistoryItem } from "../../state/types";

export default function HistoryRow({ run }: { run: RunHistoryItem }) {
  const videoHref = run.youtube_url ?? (run.video_path ? `/outputs/${run.id}/short.mp4` : null);

  return (
    <tr className="border-t border-slate-800/60 text-xs hover:bg-slate-800/20 transition-colors">
      <td className="py-2.5 pr-3 text-slate-500 whitespace-nowrap">{formatTime(run.started_at)}</td>
      <td className="py-2.5 pr-3 text-slate-300 max-w-[280px] truncate" title={run.topic ?? ""}>
        {run.topic ?? "—"}
      </td>
      <td className="py-2.5 pr-3 text-slate-400 tabular-nums">{formatScore(run.hook_score)}</td>
      <td className="py-2.5 pr-3">
        <span
          className={`px-2 py-0.5 rounded-full border text-[11px] ${
            run.status === "completed"
              ? "bg-emerald-400/10 text-emerald-400 border-emerald-400/20"
              : run.status === "failed"
                ? "bg-red-400/10 text-red-400 border-red-400/20"
                : "bg-amber-400/10 text-amber-400 border-amber-400/20"
          }`}
        >
          {run.status}
        </span>
      </td>
      <td className="py-2.5">
        {videoHref ? (
          <a href={videoHref} target="_blank" rel="noreferrer" className="text-emerald-400 hover:underline">
            {run.youtube_url ? "watch ↗" : "preview"}
          </a>
        ) : (
          <span className="text-slate-700">—</span>
        )}
      </td>
    </tr>
  );
}
