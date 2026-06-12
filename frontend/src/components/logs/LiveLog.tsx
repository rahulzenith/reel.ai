import { useEffect, useRef } from "react";

export default function LiveLog({ logs }: { logs: string[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-5 backdrop-blur flex-1 animate-fade-up">
      <p className="text-[11px] font-semibold text-slate-500 uppercase tracking-[0.15em] mb-3">Live log</p>
      <div ref={ref} className="log-scroll font-mono text-[11px] leading-5 space-y-1 max-h-64 overflow-y-auto pr-1">
        {logs.length === 0 ? (
          <p className="text-slate-700">Waiting for agents…</p>
        ) : (
          logs.map((l, i) => (
            <p
              key={`${i}-${l.slice(0, 16)}`}
              className={`animate-slide-in ${
                l.includes("failed") || l.includes("Error") || l.includes("error")
                  ? "text-red-400"
                  : l.includes("complete") || l.includes("PASS")
                    ? "text-emerald-400"
                    : "text-slate-500"
              }`}
            >
              <span className="text-slate-700 select-none">▸ </span>
              {l}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
