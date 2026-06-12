interface Props {
  label: string;
  value: number | null;
  threshold?: number;
}

export default function ScoreBar({ label, value, threshold }: Props) {
  return (
    <div className="mb-2">
      <div className="flex justify-between text-xs mb-1">
        <span className="text-gray-500">{label}</span>
        <span className="font-medium text-gray-800">{value == null ? "—" : value.toFixed(2)}</span>
      </div>
      <div className="relative h-1.5 bg-gray-100 rounded-full overflow-visible">
        <div
          className={`h-full rounded-full transition-all duration-700 ${
            value != null && threshold != null && value < threshold ? "bg-amber-400" : "bg-emerald-500"
          }`}
          style={{ width: value == null ? "0%" : `${value * 100}%` }}
        />
        {threshold != null && (
          <div
            className="absolute top-[-3px] h-3 w-px bg-gray-400"
            style={{ left: `${threshold * 100}%` }}
            title={`Pass threshold: ${threshold}`}
          />
        )}
      </div>
    </div>
  );
}
