import type { Scores } from "../../state/types";
import ScoreBar from "./ScoreBar";

interface Props {
  scores: Scores | null;
  retryCount: number;
  feedback: string | null;
}

const HOOK_THRESHOLD = 0.7;

export default function ScorePanel({ scores, retryCount, feedback }: Props) {
  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4">
      <div className="flex justify-between items-center mb-3">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Script eval</p>
        {retryCount > 1 && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
            attempt {retryCount}
          </span>
        )}
      </div>
      <ScoreBar label="Hook strength" value={scores?.hook_score ?? null} threshold={HOOK_THRESHOLD} />
      <ScoreBar label="Retention" value={scores?.retention_score ?? null} />
      <ScoreBar label="Clarity" value={scores?.clarity_score ?? null} />
      {feedback && <p className="text-xs text-gray-400 mt-2 italic">"{feedback}"</p>}
    </div>
  );
}
