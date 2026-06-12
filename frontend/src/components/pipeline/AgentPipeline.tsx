import { AGENTS, type AgentStatus } from "../../state/types";
import AgentRow from "./AgentRow";

export default function AgentPipeline({ nodes }: { nodes: Record<string, AgentStatus> }) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Agent pipeline</p>
      <div className="flex flex-col gap-2">
        {AGENTS.map((a) => (
          <AgentRow key={a.id} agent={a} status={nodes[a.id] ?? "waiting"} />
        ))}
      </div>
    </div>
  );
}
