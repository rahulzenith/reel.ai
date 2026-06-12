import type { AgentStatus } from "../../state/types";

export default function StatusBadge({ status }: { status: AgentStatus }) {
  if (status === "running")
    return (
      <span className="flex items-center gap-2">
        <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-400/10 text-emerald-400 border border-emerald-400/20">
          running
        </span>
        <span className="w-3.5 h-3.5 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
      </span>
    );
  if (status === "done")
    return (
      <span className="w-5 h-5 rounded-full bg-emerald-400/15 text-emerald-400 text-xs flex items-center justify-center animate-fade-in">
        ✓
      </span>
    );
  if (status === "error")
    return (
      <span className="text-[11px] px-2 py-0.5 rounded-full bg-red-400/10 text-red-400 border border-red-400/20">
        error
      </span>
    );
  return <span className="w-2 h-2 rounded-full bg-slate-700" />;
}
