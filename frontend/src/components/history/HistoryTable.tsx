import type { RunHistoryItem } from "../../state/types";
import HistoryRow from "./HistoryRow";

export default function HistoryTable({ runs }: { runs: RunHistoryItem[] }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 mt-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Run history</p>
      {runs.length === 0 ? (
        <p className="text-xs text-gray-300">No runs yet — hit "Run now".</p>
      ) : (
        <table className="w-full text-left">
          <thead>
            <tr className="text-xs text-gray-400">
              <th className="font-medium pb-1 pr-3">When</th>
              <th className="font-medium pb-1 pr-3">Topic</th>
              <th className="font-medium pb-1 pr-3">Hook</th>
              <th className="font-medium pb-1 pr-3">Status</th>
              <th className="font-medium pb-1">Video</th>
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
