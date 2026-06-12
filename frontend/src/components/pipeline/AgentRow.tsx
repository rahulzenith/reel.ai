import type { AgentStatus } from "../../state/types";
import StatusBadge from "./StatusBadge";

interface Props {
  agent: { id: string; label: string; sub: string };
  status: AgentStatus;
}

export default function AgentRow({ agent, status }: Props) {
  const tone =
    status === "running"
      ? "border-emerald-300 bg-emerald-50"
      : status === "error"
        ? "border-red-200 bg-red-50"
        : status === "done"
          ? "border-gray-100 bg-white opacity-70"
          : "border-gray-100 bg-white opacity-40";

  return (
    <div className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border transition-all ${tone}`}>
      <div className="flex-1 min-w-0">
        <p className={`text-sm font-medium ${status === "running" ? "text-emerald-900" : "text-gray-800"}`}>
          {agent.label}
        </p>
        <p className="text-xs text-gray-400 truncate">{agent.sub}</p>
      </div>
      <StatusBadge status={status} />
    </div>
  );
}
