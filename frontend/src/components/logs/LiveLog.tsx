import { useEffect, useRef } from "react";

export default function LiveLog({ logs }: { logs: string[] }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [logs]);

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 flex-1">
      <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-3">Live log</p>
      <div ref={ref} className="font-mono text-xs space-y-1 max-h-56 overflow-y-auto">
        {logs.length === 0 ? (
          <p className="text-gray-300">Waiting for agents...</p>
        ) : (
          logs.map((l, i) => (
            <p key={i} className={l.includes("failed") || l.includes("Error") ? "text-red-500" : "text-gray-500"}>
              {l}
            </p>
          ))
        )}
      </div>
    </div>
  );
}
