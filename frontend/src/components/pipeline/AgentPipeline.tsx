import { AGENTS, type AgentStatus } from "../../state/types";
import AgentRow from "./AgentRow";

export default function AgentPipeline({ nodes }: { nodes: Record<string, AgentStatus> }) {
  const doneCount = AGENTS.filter((a) => nodes[a.id] === "done").length;
  const progress = (doneCount / AGENTS.length) * 100;

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <div className="flex items-center justify-between mb-1">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em]">Agent pipeline</p>
        <span className="text-xs text-slate-500">
          {doneCount}/{AGENTS.length}
        </span>
      </div>
      <div className="h-1 bg-slate-800 rounded-full mb-4 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full transition-all duration-700"
          style={{ width: `${progress}%` }}
        />
      </div>
      <div className="flex flex-col gap-2">
        {AGENTS.map((a, i) => (
          <AgentRow key={a.id} agent={a} status={nodes[a.id] ?? "waiting"} index={i} />
        ))}
      </div>
    </div>
  );
}
