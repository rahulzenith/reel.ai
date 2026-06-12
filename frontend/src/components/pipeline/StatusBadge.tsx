import type { AgentStatus } from "../../state/types";

export default function StatusBadge({ status }: { status: AgentStatus }) {
  if (status === "running")
    return (
      <span className="flex items-center gap-2">
        <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">Running</span>
        <span className="w-3.5 h-3.5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
      </span>
    );
  if (status === "done") return <span className="text-emerald-500 text-sm">✓</span>;
  if (status === "error") return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Error</span>;
  return <span className="w-3 h-3 rounded-full bg-gray-200" />;
}
