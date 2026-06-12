interface Props {
  label: string;
  value: number | null;
  threshold?: number;
}

export default function ScoreBar({ label, value, threshold }: Props) {
  const below = value != null && threshold != null && value < threshold;
  return (
    <div className="mb-3">
      <div className="flex justify-between text-xs mb-1.5">
        <span className="text-slate-400">{label}</span>
        <span className={`font-semibold tabular-nums ${below ? "text-amber-400" : "text-slate-200"}`}>
          {value == null ? "—" : value.toFixed(2)}
        </span>
      </div>
      <div className="relative h-1.5 bg-slate-800 rounded-full">
        <div
          className={`h-full rounded-full transition-all duration-1000 ease-out ${
            below
              ? "bg-gradient-to-r from-amber-500 to-orange-400"
              : "bg-gradient-to-r from-emerald-500 to-teal-400"
          }`}
          style={{ width: value == null ? "0%" : `${value * 100}%` }}
        />
        {threshold != null && (
          <div
            className="absolute -top-1 h-3.5 w-px bg-slate-500"
            style={{ left: `${threshold * 100}%` }}
            title={`Pass threshold: ${threshold}`}
          />
        )}
      </div>
    </div>
  );
}
