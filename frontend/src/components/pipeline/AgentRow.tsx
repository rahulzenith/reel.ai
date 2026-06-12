import type { AgentStatus } from "../../state/types";
import StatusBadge from "./StatusBadge";

interface Props {
  agent: { id: string; label: string; sub: string };
  status: AgentStatus;
  index: number;
}

export default function AgentRow({ agent, status, index }: Props) {
  const tone =
    status === "running"
      ? "border-emerald-400/30 bg-emerald-400/[0.06] animate-glow"
      : status === "error"
        ? "border-red-400/30 bg-red-400/[0.06]"
        : status === "done"
          ? "border-slate-800 bg-slate-900/40"
          : "border-slate-800/60 bg-slate-900/20 opacity-50";

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded-xl border transition-all duration-300 animate-fade-up ${tone}`}
      style={{ animationDelay: `${index * 50}ms` }}
    >
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${status === "running" ? "text-emerald-300" : status === "done" ? "text-slate-300" : "text-slate-400"}`}>
          {agent.label}
        </p>
        <p className="text-xs text-slate-600 truncate">{agent.sub}</p>
      </div>
      <StatusBadge status={status} />
    </div>
  );
}
