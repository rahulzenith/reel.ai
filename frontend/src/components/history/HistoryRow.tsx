import { formatScore, formatTime } from "../../lib/format";
import type { RunHistoryItem } from "../../state/types";

export default function HistoryRow({ run }: { run: RunHistoryItem }) {
  const videoHref = run.youtube_url ?? (run.video_path ? `/outputs/${run.id}/short.mp4` : null);

  return (
    <tr className="border-t border-gray-50 text-xs">
      <td className="py-2 pr-3 text-gray-400 whitespace-nowrap">{formatTime(run.started_at)}</td>
      <td className="py-2 pr-3 text-gray-700 max-w-[260px] truncate" title={run.topic ?? ""}>
        {run.topic ?? "—"}
      </td>
      <td className="py-2 pr-3 text-gray-500">{formatScore(run.hook_score)}</td>
      <td className="py-2 pr-3">
        <span
          className={`px-2 py-0.5 rounded-full ${
            run.status === "completed"
              ? "bg-emerald-100 text-emerald-700"
              : run.status === "failed"
                ? "bg-red-100 text-red-700"
                : "bg-amber-100 text-amber-700"
          }`}
        >
          {run.status}
        </span>
      </td>
      <td className="py-2">
        {videoHref ? (
          <a href={videoHref} target="_blank" rel="noreferrer" className="text-emerald-600 hover:underline">
            {run.youtube_url ? "watch" : "preview"}
          </a>
        ) : (
          <span className="text-gray-300">—</span>
        )}
      </td>
    </tr>
  );
}
