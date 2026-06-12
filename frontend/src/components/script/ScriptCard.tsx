import type { ScriptData } from "../../state/types";

export default function ScriptCard({ script }: { script: ScriptData | null }) {
  if (!script) {
    return (
      <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em] mb-3">Script</p>
        <div className="flex items-center justify-center h-32 text-sm text-slate-600">
          The script appears here as soon as it's written…
        </div>
      </div>
    );
  }

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur animate-fade-up">
      <div className="flex items-center justify-between mb-4">
        <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em]">Script</p>
        <span className="text-xs text-slate-500">{script.full_text.split(/\s+/).length} words</span>
      </div>

      {/* Hook — the money line */}
      <div className="border-l-2 border-emerald-400 pl-4 mb-4 animate-slide-in">
        <p className="text-[10px] uppercase tracking-widest text-emerald-500 mb-1">Hook</p>
        <p className="text-lg font-semibold text-white leading-snug">{script.hook}</p>
      </div>

      <div className="mb-4 animate-fade-in" style={{ animationDelay: "150ms" }}>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Body</p>
        <p className="text-sm text-slate-300 leading-relaxed">{script.body}</p>
      </div>

      <div className="mb-4 animate-fade-in" style={{ animationDelay: "300ms" }}>
        <p className="text-[10px] uppercase tracking-widest text-slate-500 mb-1">Call to action</p>
        <p className="text-sm text-teal-300 italic">{script.cta}</p>
      </div>

      <div className="pt-3 border-t border-slate-800 flex flex-wrap items-center gap-2 animate-fade-in" style={{ animationDelay: "400ms" }}>
        <span className="text-xs text-slate-400 mr-1" title="YouTube title">
          🎬 {script.title}
        </span>
        {script.keywords?.map((k) => (
          <span
            key={k}
            className="text-[11px] px-2 py-0.5 rounded-full bg-indigo-400/10 text-indigo-300 border border-indigo-400/20"
            title="B-roll search keyword"
          >
            {k}
          </span>
        ))}
      </div>
    </div>
  );
}
