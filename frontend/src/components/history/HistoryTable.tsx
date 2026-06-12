import type { RunHistoryItem } from "../../state/types";
import HistoryRow from "./HistoryRow";

export default function HistoryTable({ runs }: { runs: RunHistoryItem[] }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em] mb-3">Run history</p>
      {runs.length === 0 ? (
        <p className="text-xs text-slate-600">No runs yet — hit “Run now”.</p>
      ) : (
        <table className="w-full text-left">
          <thead>
            <tr className="text-[11px] text-slate-600 uppercase tracking-wider">
              <th className="font-medium pb-2 pr-3">When</th>
              <th className="font-medium pb-2 pr-3">Topic</th>
              <th className="font-medium pb-2 pr-3">Hook</th>
              <th className="font-medium pb-2 pr-3">Status</th>
              <th className="font-medium pb-2">Video</th>
            </tr>
          </thead>
          <tbody>
            {runs.map((r) => (
              <HistoryRow key={r.id} run={r} />
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
